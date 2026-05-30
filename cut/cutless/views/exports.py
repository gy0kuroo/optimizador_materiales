from decimal import Decimal

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from ..models import Optimizacion
from ..services import (
    calcular_numero_lista,
    convertir_info_desperdicio_unidad,
    nombre_descarga_excel,
    obtener_resultado_optimizacion,
    respuesta_png_tablero,
    respuesta_pdf_optimizacion,
)
from ..utils import (
    convertir_a_cm,
    convertir_desde_cm,
    generar_excel,
    generar_grafico,
    obtener_simbolo_area,
    obtener_simbolo_unidad,
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
    API que retorna todas las imágenes de tableros de una optimización en base64.
    """
    from django.http import JsonResponse

    optimizacion = get_object_or_404(Optimizacion, pk=pk, usuario=request.user)
    imagenes_base64, _, _ = obtener_resultado_optimizacion(
        optimizacion,
        persistir_si_falta=True,
    )

    return JsonResponse({
        'success': True,
        'imagenes': imagenes_base64,
        'total': len(imagenes_base64)
    })

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
    
    # Recuperar datos de la optimización guardada
    unidad = getattr(optimizacion, 'unidad_medida', 'cm') or 'cm'
    
    # Parsear piezas
    piezas_con_nombre = []
    for linea in optimizacion.piezas.splitlines():
        if linea.strip():
            partes = linea.split(',')
            if len(partes) == 4:
                ancho = float(partes[1].strip())
                alto = float(partes[2].strip())
                cantidad = int(partes[3].strip())
                area_unitaria = ancho * alto
                area_total = area_unitaria * cantidad
                piezas_con_nombre.append({
                    'nombre': partes[0].strip(),
                    'ancho': ancho,
                    'alto': alto,
                    'cantidad': cantidad,
                    'area_unitaria': area_unitaria,
                    'area_total': area_total
                })
    
    # Regenerar la optimización para obtener todas las imágenes y detalles
    piezas_para_optimizar = []
    nombres_piezas = []
    for pieza in piezas_con_nombre:
        ancho_val = pieza['ancho']
        alto_val = pieza['alto']
        cantidad = pieza['cantidad']
        nombre = pieza['nombre']
        
        # Convertir a cm si es necesario
        ancho_cm = convertir_a_cm(ancho_val, unidad)
        alto_cm = convertir_a_cm(alto_val, unidad)
        
        # Agregar como tupla de 3 elementos (ancho, alto, cantidad)
        piezas_para_optimizar.append((ancho_cm, alto_cm, cantidad))
        nombres_piezas.append(nombre)
    
    # Obtener parámetros de la optimización
    margen_corte = getattr(optimizacion, 'margen_corte', 0.3) or 0.3
    permitir_rotacion = getattr(optimizacion, 'permitir_rotacion', True)
    
    # Regenerar gráfico en modo plan de corte (blanco y negro, solo medidas)
    imagenes_base64, aprovechamiento, info_desperdicio = generar_grafico(
        piezas_para_optimizar,
        optimizacion.ancho_tablero,
        optimizacion.alto_tablero,
        unidad='cm',
        permitir_rotacion=permitir_rotacion,
        margen_corte=margen_corte,
        nombres_piezas=nombres_piezas if nombres_piezas else None,
        modo_plan_corte=True  # Modo blanco y negro para plan de corte
    )
    
    num_tableros = len(imagenes_base64)
    
    simbolo_area = obtener_simbolo_area(unidad)
    simbolo_unidad = obtener_simbolo_unidad(unidad)
    info_desperdicio_mostrar = convertir_info_desperdicio_unidad(
        info_desperdicio, unidad, optimizacion,
    )
    info_tableros_convertida = info_desperdicio_mostrar['info_tableros']
    
    # Combinar imágenes con información de tableros
    tableros_con_imagenes = []
    for idx, (img, info) in enumerate(zip(imagenes_base64, info_tableros_convertida), start=1):
        tableros_con_imagenes.append({
            'numero': info['numero'],
            'imagen': img,
            'info': info
        })
    
    # Calcular costos
    costo_total = optimizacion.get_costo_total()
    costo_material = None
    precio_tablero = optimizacion.precio_tablero
    mano_obra = optimizacion.mano_obra or Decimal('0.00')
    
    if precio_tablero:
        costo_material = Decimal(str(num_tableros)) * precio_tablero
    
    # Calcular número de lista
    todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user).order_by('-fecha')
    total_optimizaciones = todas_optimizaciones.count()
    
    numero_lista = optimizacion.pk
    for idx, opt in enumerate(todas_optimizaciones, start=1):
        if opt.id == optimizacion.id:
            numero_lista = total_optimizaciones - idx + 1
            break
    
    return render(request, "cutless/imprimir_plan_corte.html", {
        "optimizacion": optimizacion,
        "imagenes": imagenes_base64,
        "num_tableros": num_tableros,
        "piezas_con_nombre": piezas_con_nombre,
        "info_desperdicio": info_desperdicio_mostrar,
        "tableros_con_imagenes": tableros_con_imagenes,
        "numero_lista": numero_lista,
        "unidad_medida": unidad,
        "simbolo_area": simbolo_area,
        "simbolo_unidad": simbolo_unidad,
        "costo_total": costo_total,
        "costo_material": costo_material,
        "precio_tablero": precio_tablero,
        "mano_obra": mano_obra,
    })

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

