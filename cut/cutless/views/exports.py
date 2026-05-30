# Imports estándar de Python
import base64
import os
from datetime import timedelta
from decimal import Decimal

# Imports de Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db.models import Avg, Count, Sum, Max, Min, Q
from django.forms import formset_factory
from django.http import FileResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.utils import timezone

# Imports del proyecto
from django.conf import settings
from ..forms import TableroForm, PiezaForm, MaterialForm, ClienteForm, PresupuestoForm, ProyectoForm, PlantillaForm
from ..models import Optimizacion, Material, Cliente, Presupuesto, Proyecto, Plantilla
from ..utils import (
    convertir_a_cm, convertir_desde_cm, generar_excel, generar_grafico,
    generar_grafico_aprovechamiento, generar_grafico_desperdicio, generar_pdf,
    generar_excel_resumen_desperdicio, generar_pdf_resumen_desperdicio,
    mensaje_advertencia_piezas_no_colocadas, obtener_simbolo_area, obtener_simbolo_unidad,
    parsear_piezas_desde_texto,
    pieza_cabe_en_tablero,
)
from ..utils_notificaciones import enviar_notificacion
from ..services import (
    calcular_numero_lista,
    nombre_descarga_excel,
    persistir_resultado_optimizacion,
    obtener_resultado_optimizacion,
    preparar_contexto_resultado,
    pdf_path_para_template,
    respuesta_png_tablero,
    respuesta_pdf_optimizacion,
)
from .common import _materiales_data_json_index, requiere_permiso
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

    factor_area = convertir_desde_cm(1, unidad_opt) ** 2
    info_desperdicio_convertida = {
        'area_usada_total': round(info_desperdicio['area_usada_total'] * factor_area, 2),
        'desperdicio_total': round(info_desperdicio['desperdicio_total'] * factor_area, 2),
        'info_tableros': [
            {
                **info,
                'area_usada': round(info['area_usada'] * factor_area, 2),
                'desperdicio': round(info['desperdicio'] * factor_area, 2),
            }
            for info in info_desperdicio['info_tableros']
        ]
    }

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
    
    # Convertir áreas a la unidad del usuario
    simbolo_area = obtener_simbolo_area(unidad)
    simbolo_unidad = obtener_simbolo_unidad(unidad)
    factor_lineal = convertir_desde_cm(1, unidad)
    factor_area = factor_lineal ** 2
    
    area_usada_mostrar = round(info_desperdicio['area_usada_total'] * factor_area, 2)
    desperdicio_mostrar = round(info_desperdicio['desperdicio_total'] * factor_area, 2)
    
    # Convertir info de tableros
    info_tableros_convertida = []
    for info in info_desperdicio['info_tableros']:
        area_usada_tab = round(info['area_usada'] * factor_area, 2)
        desperdicio_tab = round(info['desperdicio'] * factor_area, 2)
        info_tableros_convertida.append({
            **info,
            'area_usada': area_usada_tab,
            'desperdicio': desperdicio_tab,
        })
    
    info_desperdicio_mostrar = {
        **info_desperdicio,
        'area_usada_total': area_usada_mostrar,
        'desperdicio_total': desperdicio_mostrar,
        'info_tableros': info_tableros_convertida,
    }
    
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

