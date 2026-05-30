import base64
import os

from django.conf import settings
from django.core.files.base import ContentFile
from django.http import FileResponse
from django.utils import timezone

from ..models import Optimizacion, TableroOptimizacion
from ..utils import (
    convertir_desde_cm,
    generar_grafico,
    generar_pdf,
    obtener_simbolo_area,
    parsear_piezas_desde_texto,
)


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


def _guardar_pdf_en_modelo(optimizacion, pdf_filepath):
    pdf_filepath = _normalizar_ruta_absoluta(pdf_filepath)
    if not pdf_filepath or not os.path.isfile(pdf_filepath):
        return None
    if optimizacion.pdf:
        optimizacion.pdf.delete(save=False)
    storage_name = f"opt_{optimizacion.pk}.pdf"
    with open(pdf_filepath, 'rb') as pdf_file:
        optimizacion.pdf.save(
            storage_name,
            ContentFile(pdf_file.read()),
            save=True,
        )
    return pdf_filepath


def _generar_y_guardar_pdf(optimizacion, imagenes_base64, info_desperdicio, numero_lista=None):
    lista = numero_lista if numero_lista is not None else optimizacion.pk
    pdf_filepath = generar_pdf(
        optimizacion,
        imagenes_base64,
        numero_lista=lista,
        info_desperdicio=info_desperdicio,
    )
    pdf_filepath = _normalizar_ruta_absoluta(pdf_filepath)
    if pdf_filepath and os.path.isfile(pdf_filepath):
        _guardar_pdf_en_modelo(optimizacion, pdf_filepath)
    return pdf_filepath


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
    return {
        'area_usada_total': optimizacion.area_usada_total or 0,
        'desperdicio_total': optimizacion.desperdicio_total or 0,
        'info_tableros': info_tableros,
        'num_tableros': len(info_tableros),
        'piezas_no_colocadas': extra.get('piezas_no_colocadas', []),
        'num_piezas_solicitadas': extra.get('num_piezas_solicitadas', 0),
        'num_piezas_colocadas': extra.get('num_piezas_colocadas', 0),
    }


def _regenerar_grafico(optimizacion):
    unidad = getattr(optimizacion, 'unidad_medida', 'cm') or 'cm'
    piezas_parseadas = parsear_piezas_desde_texto(optimizacion.piezas, unidad)
    piezas = [(p['ancho_cm'], p['alto_cm'], p['cantidad']) for p in piezas_parseadas]
    nombres = [p['nombre'] for p in piezas_parseadas]
    margen = getattr(optimizacion, 'margen_corte', 0.3) or 0.3
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
    """Guarda tableros, estadísticas y PDF tras generar_grafico."""
    optimizacion.tableros.all().delete()

    info_tableros = info_desperdicio.get('info_tableros') or []
    for indice, imagen_b64 in enumerate(imagenes_base64):
        info = info_tableros[indice] if indice < len(info_tableros) else {}
        numero = info.get('numero', indice + 1)
        tablero = TableroOptimizacion(
            optimizacion=optimizacion,
            numero=numero,
            area_usada=info.get('area_usada', 0),
            desperdicio=info.get('desperdicio', 0),
            porcentaje_uso=info.get('porcentaje_uso', 0),
            num_piezas=info.get('num_piezas', 0),
        )
        nombre = f"opt_{optimizacion.pk}_tablero_{numero}.png"
        tablero.imagen.save(
            nombre,
            ContentFile(base64.b64decode(imagen_b64)),
            save=True,
        )

    if imagenes_base64:
        nombre_preview = f"opt_{optimizacion.pk}_preview.png"
        optimizacion.imagen.save(
            nombre_preview,
            ContentFile(base64.b64decode(imagenes_base64[0])),
            save=False,
        )

    optimizacion.aprovechamiento_total = aprovechamiento
    optimizacion.area_usada_total = info_desperdicio.get('area_usada_total', 0)
    optimizacion.desperdicio_total = info_desperdicio.get('desperdicio_total', 0)
    optimizacion.num_tableros = len(imagenes_base64)
    optimizacion.resultado_generado = True
    optimizacion.resultado_generado_en = timezone.now()
    optimizacion.resultado_extra = {
        'piezas_no_colocadas': info_desperdicio.get('piezas_no_colocadas', []),
        'num_piezas_solicitadas': info_desperdicio.get('num_piezas_solicitadas', 0),
        'num_piezas_colocadas': info_desperdicio.get('num_piezas_colocadas', 0),
    }

    lista = numero_lista if numero_lista is not None else optimizacion.pk
    _generar_y_guardar_pdf(optimizacion, imagenes_base64, info_desperdicio, numero_lista=lista)

    optimizacion.save()
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
    if persistir_si_falta and imagenes:
        persistir_resultado_optimizacion(
            optimizacion,
            imagenes,
            info,
            aprovechamiento,
            numero_lista=numero_lista,
        )
    return imagenes, aprovechamiento, info


def preparar_contexto_resultado(optimizacion, imagenes_base64, info_desperdicio, piezas_parseadas=None):
    """Construye el contexto de visualización para resultado.html."""
    unidad = getattr(optimizacion, 'unidad_medida', 'cm') or 'cm'
    simbolo_area = obtener_simbolo_area(unidad)
    factor_area = convertir_desde_cm(1, unidad) ** 2

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

    info_tableros_convertida = []
    for info in info_desperdicio.get('info_tableros', []):
        info_tableros_convertida.append({
            **info,
            'area_usada': round(info['area_usada'] * factor_area, 2),
            'desperdicio': round(info['desperdicio'] * factor_area, 2),
        })

    info_desperdicio_mostrar = {
        **info_desperdicio,
        'area_usada_total': round(info_desperdicio['area_usada_total'] * factor_area, 2),
        'desperdicio_total': round(info_desperdicio['desperdicio_total'] * factor_area, 2),
        'info_tableros': info_tableros_convertida,
    }

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
