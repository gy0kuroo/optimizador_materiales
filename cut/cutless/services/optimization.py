import base64
import io
import logging
import os
from uuid import uuid4

from django.conf import settings
from django.core.files.base import ContentFile
from django.http import FileResponse
from django.db import transaction
from django.utils import timezone

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


def _guardar_archivo(field, nombre, contenido, archivos_nuevos):
    # Registrar el nombre antes de escribir permite retirar una escritura parcial.
    ruta = field.field.generate_filename(field.instance, nombre)
    archivos_nuevos.append((field.storage, ruta))
    guardado = field.storage.save(ruta, ContentFile(contenido))
    if guardado != ruta:
        archivos_nuevos.append((field.storage, guardado))
    field.name = guardado
    field._committed = True


def _crear_pdf(optimizacion, imagenes_base64, info_desperdicio, archivos_nuevos, numero_lista=None):
    buffer = io.BytesIO()
    resultado = generar_pdf(
        optimizacion, imagenes_base64,
        numero_lista=numero_lista if numero_lista is not None else optimizacion.pk,
        info_desperdicio=info_desperdicio,
        archivo_salida=buffer,
    )
    if resultado is None or not buffer.getvalue():
        raise ValueError("No se generó el PDF de la optimización.")
    _guardar_archivo(
        optimizacion.pdf, f"opt_{optimizacion.pk}_{uuid4().hex}.pdf",
        buffer.getvalue(), archivos_nuevos,
    )


def _generar_y_guardar_pdf(optimizacion, imagenes_base64, info_desperdicio, numero_lista=None):
    nuevos = []
    try:
        with transaction.atomic():
            anterior = Optimizacion.objects.select_for_update().get(pk=optimizacion.pk)
            antiguos = [(anterior.pdf.storage, anterior.pdf.name)] if anterior.pdf else []
            _crear_pdf(optimizacion, imagenes_base64, info_desperdicio, nuevos, numero_lista)
            optimizacion.save(update_fields=['pdf'])
            transaction.on_commit(lambda: _eliminar_archivos(antiguos))
    except Exception:
        _eliminar_archivos(nuevos)
        optimizacion.refresh_from_db()
        raise
    return _ruta_pdf_en_disco(optimizacion)


def _numero_descarga(numero_lista, optimizacion):
    return numero_lista if numero_lista is not None else optimizacion.pk


def nombre_descarga_pdf(numero_lista, optimizacion):
    return f"optimizacion_{_numero_descarga(numero_lista, optimizacion)}.pdf"


def nombre_descarga_png(numero_lista, optimizacion, tablero_num=None):
    """Nombre al descargar PNG (tablero_num no se incluye en el nombre)."""
    return f"optimizacion_{_numero_descarga(numero_lista, optimizacion)}.png"


def nombre_descarga_png_tablero(numero_lista, optimizacion, tablero_num):
    return nombre_descarga_png(numero_lista, optimizacion, tablero_num)


def nombre_descarga_excel(numero_lista, optimizacion):
    return f"optimizacion_{_numero_descarga(numero_lista, optimizacion)}.xlsx"


def calcular_numero_lista(usuario, optimizacion_id, ordenar_por='fecha_desc'):
    """Calcula el número de visualización en el historial."""
    queryset = Optimizacion.objects.filter(usuario=usuario)

    if ordenar_por == 'fecha_desc':
        queryset = queryset.order_by('-fecha')
    elif ordenar_por == 'fecha_asc':
        queryset = queryset.order_by('fecha')
    elif ordenar_por == 'aprovechamiento_desc':
        queryset = queryset.order_by('-aprovechamiento_total')
    elif ordenar_por == 'aprovechamiento_asc':
        queryset = queryset.order_by('aprovechamiento_total')
    else:
        queryset = queryset.order_by('-fecha')

    total = queryset.count()
    es_descendente = ordenar_por in ('fecha_desc', 'aprovechamiento_desc')

    for idx, opt in enumerate(queryset, start=1):
        if opt.id == optimizacion_id:
            if es_descendente:
                return total - idx + 1
            return idx

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
    for tablero in optimizacion.tableros.order_by('numero'):
        info_tableros.append({
            'numero': tablero.numero,
            'area_usada': tablero.area_usada,
            'desperdicio': tablero.desperdicio,
            'porcentaje_uso': tablero.porcentaje_uso,
            'num_piezas': tablero.num_piezas,
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
    imagenes = [base64.b64decode(imagen, validate=True) for imagen in imagenes_base64]
    nuevos = []
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

            version = uuid4().hex
            tableros = []
            for imagen, datos in zip(imagenes, info['info_tableros']):
                numero = datos['numero']
                tablero = TableroOptimizacion(
                    optimizacion=optimizacion, numero=numero,
                    area_usada=datos.get('area_usada', 0), desperdicio=datos.get('desperdicio', 0),
                    porcentaje_uso=datos.get('porcentaje_uso', 0), num_piezas=datos.get('num_piezas', 0),
                )
                _guardar_archivo(tablero.imagen, f"opt_{optimizacion.pk}_{version}_tablero_{numero}.png", imagen, nuevos)
                tableros.append(tablero)
            _guardar_archivo(optimizacion.imagen, f"opt_{optimizacion.pk}_{version}_preview.png", imagenes[0], nuevos)
            optimizacion.aprovechamiento_total = aprovechamiento
            optimizacion.area_usada_total = info['area_usada_total']
            optimizacion.desperdicio_total = info['desperdicio_total']
            optimizacion.num_tableros = len(imagenes)
            optimizacion.resultado_generado = True
            optimizacion.resultado_generado_en = timezone.now()
            optimizacion.resultado_extra = {
                clave: info[clave] for clave in ('piezas_no_colocadas', 'num_piezas_solicitadas', 'num_piezas_colocadas')
            }
            _crear_pdf(optimizacion, imagenes_base64, info, nuevos, numero_lista)
            optimizacion.tableros.all().delete()
            for tablero in tableros:
                tablero.save()
            optimizacion.save()
            transaction.on_commit(lambda: _eliminar_archivos(antiguos))
    except Exception:
        _eliminar_archivos(nuevos)
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
    Usa datos persistidos o regenera (y opcionalmente persiste) para registros legacy.
    """
    if optimizacion.resultado_generado and optimizacion.tableros.exists():
        imagenes = _cargar_imagenes_persistidas(optimizacion)
        if imagenes is not None:
            info = _info_desperdicio_desde_modelo(optimizacion)
            if persistir_si_falta and not _ruta_pdf_en_disco(optimizacion) and imagenes:
                _generar_y_guardar_pdf(optimizacion, imagenes, info, numero_lista=numero_lista)
            return imagenes, optimizacion.aprovechamiento_total, info

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
        tableros_con_imagenes.append({
            'numero': info['numero'],
            'imagen': imagen,
            'info': info,
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
    """Devuelve FileResponse del PDF persistido o lo regenera si falta."""
    nombre_descarga = nombre_descarga_pdf(numero_lista, optimizacion)
    ruta = _ruta_pdf_en_disco(optimizacion)
    if ruta:
        return FileResponse(
            open(ruta, 'rb'),
            as_attachment=True,
            filename=nombre_descarga,
        )

    imagenes, _, info = obtener_resultado_optimizacion(
        optimizacion,
        numero_lista=numero_lista,
        persistir_si_falta=True,
    )

    optimizacion.refresh_from_db()
    ruta = _ruta_pdf_en_disco(optimizacion)
    if not ruta:
        ruta = _generar_y_guardar_pdf(optimizacion, imagenes, info, numero_lista=numero_lista)

    ruta = _normalizar_ruta_absoluta(ruta)
    if not ruta or not os.path.isfile(ruta):
        raise FileNotFoundError(f'No se pudo generar el PDF de la optimización #{optimizacion.pk}')

    return FileResponse(
        open(ruta, 'rb'),
        as_attachment=True,
        filename=nombre_descarga,
    )


def respuesta_png_tablero(optimizacion, tablero_num, numero_lista=None):
    """Devuelve FileResponse del PNG persistido de un tablero."""
    nombre_descarga = nombre_descarga_png_tablero(numero_lista, optimizacion, tablero_num)
    tablero = optimizacion.tableros.filter(numero=tablero_num).first()
    if tablero and tablero.imagen:
        return FileResponse(
            tablero.imagen.open('rb'),
            as_attachment=True,
            filename=nombre_descarga,
        )

    imagenes, _, _ = obtener_resultado_optimizacion(
        optimizacion,
        numero_lista=numero_lista,
        persistir_si_falta=True,
    )
    tablero = optimizacion.tableros.filter(numero=tablero_num).first()
    if tablero and tablero.imagen:
        return FileResponse(
            tablero.imagen.open('rb'),
            as_attachment=True,
            filename=nombre_descarga,
        )

    if tablero_num < 1 or tablero_num > len(imagenes):
        return None

    from django.core.files.base import ContentFile
    image_data = base64.b64decode(imagenes[tablero_num - 1])
    return FileResponse(
        ContentFile(image_data),
        as_attachment=True,
        filename=nombre_descarga,
    )
