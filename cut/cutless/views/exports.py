from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from ..models import Optimizacion
from ..services import (
    calcular_numero_lista,
    convertir_info_desperdicio_unidad,
    nombre_descarga_excel,
    obtener_resultado_optimizacion,
    preparar_contexto_resultado,
    respuesta_png_tablero,
    respuesta_pdf_optimizacion,
)
from ..utils import (
    generar_excel,
    parsear_piezas_desde_texto,
)


def descargar_excel(request, pk):
    """
    Descarga un archivo Excel con la información detallada de la optimización.
    """
    optimizacion = get_object_or_404(Optimizacion, pk=pk, usuario=request.user)
    ordenar_por = request.GET.get('ordenar_por', 'fecha_desc')
    numero_lista = calcular_numero_lista(request.user, optimizacion.id, ordenar_por)

    unidad_opt = getattr(optimizacion, 'unidad_medida', 'cm') or 'cm'
    piezas_parseadas = parsear_piezas_desde_texto(optimizacion.piezas, unidad_opt)
    piezas_con_nombre = [
        {
            'nombre': p['nombre'],
            'ancho': p['ancho'],
            'alto': p['alto'],
            'cantidad': p['cantidad'],
        }
        for p in piezas_parseadas
    ]

    _, _, info_desperdicio = obtener_resultado_optimizacion(
        optimizacion,
        numero_lista=numero_lista,
        persistir_si_falta=True,
    )

    info_desperdicio_convertida = convertir_info_desperdicio_unidad(
        info_desperdicio, unidad_opt, optimizacion,
    )

    excel_buffer = generar_excel(optimizacion, info_desperdicio_convertida, piezas_con_nombre, numero_lista)

    from django.http import HttpResponse
    response = HttpResponse(
        excel_buffer.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{nombre_descarga_excel(numero_lista, optimizacion)}"'
    return response


def api_tableros_optimizacion(request, pk):
    """
    Imágenes generadas en memoria y presentación web de la geometría guardada.
    """
    from django.http import JsonResponse

    optimizacion = get_object_or_404(Optimizacion, pk=pk, usuario=request.user)
    imagenes_base64, _, info = obtener_resultado_optimizacion(
        optimizacion,
        persistir_si_falta=True,
    )

    respuesta = {
        'success': True,
        'imagenes': imagenes_base64,
        'total': len(imagenes_base64)
    }
    if request.GET.get('presentacion') == 'horizontal':
        from django.template.loader import render_to_string
        contexto = preparar_contexto_resultado(optimizacion, imagenes_base64, info)
        respuesta['paneles'] = [
            render_to_string('cutless/includes/board-layout.html', {**contexto, 'item': item}, request=request)
            for item in contexto['tableros_con_imagenes']
        ]
    return JsonResponse(respuesta)

def descargar_pdf(request, pk):
    optimizacion = get_object_or_404(Optimizacion, pk=pk, usuario=request.user)
    ordenar_por = request.GET.get('ordenar_por', 'fecha_desc')
    numero_lista = calcular_numero_lista(request.user, optimizacion.id, ordenar_por)
    return respuesta_pdf_optimizacion(optimizacion, numero_lista=numero_lista)

def imprimir_plan_corte(request, pk):
    """
    Vista para imprimir el plan de corte de una optimización.
    Renderiza un template optimizado para impresión.
    """
    optimizacion = get_object_or_404(Optimizacion, pk=pk, usuario=request.user)
    
    imagenes, _, info = obtener_resultado_optimizacion(optimizacion, persistir_si_falta=True)
    contexto = preparar_contexto_resultado(optimizacion, imagenes, info)
    contexto['numero_lista'] = calcular_numero_lista(request.user, optimizacion.id, 'fecha_desc')
    return render(request, 'cutless/imprimir_plan_corte.html', contexto)


def descargar_png(request, pk, tablero_num=None):
    """
    Descarga una imagen PNG de un tablero específico de una optimización.
    Si tablero_num no se especifica, descarga la primera imagen (tablero 1).
    """
    optimizacion = get_object_or_404(Optimizacion, pk=pk, usuario=request.user)
    ordenar_por = request.GET.get('ordenar_por', 'fecha_desc')
    numero_lista = calcular_numero_lista(request.user, optimizacion.id, ordenar_por)

    if tablero_num is None:
        tablero_num = 1

    respuesta = respuesta_png_tablero(optimizacion, tablero_num, numero_lista=numero_lista)
    if respuesta is None:
        messages.error(request, f"El tablero #{tablero_num} no existe.")
        return redirect('cutless:historial')
    return respuesta

