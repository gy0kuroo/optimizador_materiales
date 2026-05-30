import os
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.db.models import Avg
from django.http import FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from ..models import Optimizacion
from ..utils import (
    convertir_a_cm,
    convertir_desde_cm,
    generar_excel_historial_costos,
    generar_excel_resumen_desperdicio,
    generar_grafico,
    generar_grafico_aprovechamiento,
    generar_grafico_desperdicio,
    generar_pdf_resumen_desperdicio,
    parsear_piezas_desde_texto,
)


def calcular_tiempo_corte(request, pk):
    """
    Calcula el tiempo estimado de corte para una optimización.
    Considera: número de piezas, tipo de corte, material, etc.
    """
    optimizacion = get_object_or_404(Optimizacion, pk=pk, usuario=request.user)
    
    # Obtener parámetros de cálculo (pueden venir del POST o usar valores por defecto)
    velocidad_corte = float(request.POST.get('velocidad_corte', 2.0))  # cm/segundo (por defecto)
    tiempo_setup = float(request.POST.get('tiempo_setup', 5.0))  # minutos por tablero
    tiempo_cambio_herramienta = float(request.POST.get('tiempo_cambio_herramienta', 2.0))  # minutos
    
    # Parsear piezas (formato con nombre o legacy de 3 campos)
    piezas_parseadas = parsear_piezas_desde_texto(
        optimizacion.piezas,
        getattr(optimizacion, 'unidad_medida', 'cm') or 'cm',
    )
    total_piezas = 0
    perimetro_total = 0

    for pieza in piezas_parseadas:
        cantidad = pieza['cantidad']
        total_piezas += cantidad
        perimetro_pieza = 2 * (pieza['ancho_cm'] + pieza['alto_cm'])
        perimetro_total += perimetro_pieza * cantidad

    area_tablero = optimizacion.ancho_tablero * optimizacion.alto_tablero
    area_total_piezas = sum(
        p['ancho_cm'] * p['alto_cm'] * p['cantidad']
        for p in piezas_parseadas
    )
    num_tableros_estimado = max(1, int(area_total_piezas / area_tablero) + 1) if area_tablero > 0 else 1
    tipos_piezas = len(piezas_parseadas)
    # Calcular tiempos
    # Tiempo de corte = perímetro total / velocidad de corte
    tiempo_corte_segundos = perimetro_total / velocidad_corte
    tiempo_corte_minutos = tiempo_corte_segundos / 60
    
    # Tiempo de setup (preparación de cada tablero)
    tiempo_setup_total = tiempo_setup * num_tableros_estimado
    
    # Tiempo de cambio de herramienta (estimado: 1 cambio por cada tipo de pieza distinto)
    cambios_herramienta = max(0, tipos_piezas - 1)
    tiempo_cambio_total = tiempo_cambio_herramienta * cambios_herramienta
    
    # Tiempo total estimado
    tiempo_total_minutos = tiempo_corte_minutos + tiempo_setup_total + tiempo_cambio_total
    tiempo_total_horas = tiempo_total_minutos / 60
    
    # Formatear tiempo
    horas = int(tiempo_total_horas)
    minutos = int(tiempo_total_minutos % 60)
    segundos = int((tiempo_total_minutos % 1) * 60)
    
    # Calcular porcentajes
    porcentaje_corte = round((tiempo_corte_minutos / tiempo_total_minutos * 100) if tiempo_total_minutos > 0 else 0, 1)
    porcentaje_setup = round((tiempo_setup_total / tiempo_total_minutos * 100) if tiempo_total_minutos > 0 else 0, 1)
    porcentaje_cambio = round((tiempo_cambio_total / tiempo_total_minutos * 100) if tiempo_total_minutos > 0 else 0, 1)
    
    # Preparar datos para mostrar
    unidad_opt = getattr(optimizacion, 'unidad_medida', 'cm') or 'cm'
    ancho_mostrar = round(convertir_desde_cm(optimizacion.ancho_tablero, unidad_opt), 2)
    alto_mostrar = round(convertir_desde_cm(optimizacion.alto_tablero, unidad_opt), 2)
    
    return render(request, 'cutless/calcular_tiempo.html', {
        'optimizacion': optimizacion,
        'ancho_mostrar': ancho_mostrar,
        'alto_mostrar': alto_mostrar,
        'unidad_medida': unidad_opt,
        'total_piezas': total_piezas,
        'tipos_piezas': tipos_piezas,
        'num_tableros_estimado': num_tableros_estimado,
        'perimetro_total': round(perimetro_total, 2),
        'tiempo_corte_minutos': round(tiempo_corte_minutos, 2),
        'tiempo_setup_total': round(tiempo_setup_total, 2),
        'tiempo_cambio_total': round(tiempo_cambio_total, 2),
        'tiempo_total_minutos': round(tiempo_total_minutos, 2),
        'tiempo_total_horas': round(tiempo_total_horas, 2),
        'tiempo_formateado': f"{horas}h {minutos}m {segundos}s" if horas > 0 else f"{minutos}m {segundos}s",
        'velocidad_corte': velocidad_corte,
        'tiempo_setup': tiempo_setup,
        'tiempo_cambio_herramienta': tiempo_cambio_herramienta,
        'porcentaje_corte': porcentaje_corte,
        'porcentaje_setup': porcentaje_setup,
        'porcentaje_cambio': porcentaje_cambio,
        'velocidad_corte_cm_min': round(velocidad_corte * 60, 0),
    })

def exportar_pdf_desperdicio(request):
    """
    Exporta un PDF con el resumen de desperdicio desde estadísticas.
    """
    try:
        # Obtener todas las optimizaciones del usuario
        todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user)
        
        # Obtener período seleccionado
        periodo = request.GET.get('periodo', 'todos')
        
        # Filtrar por período
        ahora = timezone.now()
        optimizaciones_filtradas = todas_optimizaciones
        
        if periodo == 'semanal':
            fecha_limite = ahora - timedelta(days=7)
            optimizaciones_filtradas = todas_optimizaciones.filter(fecha__gte=fecha_limite)
        elif periodo == 'mensual':
            fecha_limite = ahora - timedelta(days=30)
            optimizaciones_filtradas = todas_optimizaciones.filter(fecha__gte=fecha_limite)
        elif periodo == 'anual':
            fecha_limite = ahora - timedelta(days=365)
            optimizaciones_filtradas = todas_optimizaciones.filter(fecha__gte=fecha_limite)
        
        # Calcular estadísticas
        total_optimizaciones = optimizaciones_filtradas.count()
        
        if total_optimizaciones > 0:
            promedio_aprovechamiento = optimizaciones_filtradas.aggregate(
                avg=Avg('aprovechamiento_total')
            )['avg'] or 0
            max_aprovechamiento = optimizaciones_filtradas.order_by('-aprovechamiento_total').first()
            max_aprovech_val = max_aprovechamiento.aprovechamiento_total if max_aprovechamiento else 0
            min_aprovechamiento = optimizaciones_filtradas.order_by('aprovechamiento_total').first()
            min_aprovech_val = min_aprovechamiento.aprovechamiento_total if min_aprovechamiento else 0
            promedio_desperdicio = 100 - promedio_aprovechamiento
        else:
            promedio_aprovechamiento = 0
            max_aprovech_val = 0
            min_aprovech_val = 0
            promedio_desperdicio = 0
        
        estadisticas = {
            'total_optimizaciones': total_optimizaciones,
            'promedio_aprovechamiento': promedio_aprovechamiento,
            'max_aprovechamiento': max_aprovech_val,
            'min_aprovechamiento': min_aprovech_val,
            'promedio_desperdicio': promedio_desperdicio,
        }
        
        # Generar PDF
        pdf_path = generar_pdf_resumen_desperdicio(optimizaciones_filtradas, estadisticas, periodo)
        
        # pdf_path ya es relativo (pdfs/filename.pdf)
        full_path = os.path.join(settings.MEDIA_ROOT, pdf_path)
        filename = os.path.basename(pdf_path)
        return FileResponse(open(full_path, "rb"), as_attachment=True, filename=filename)
        
    except Exception as e:
        messages.error(request, f"Error generando PDF: {e}")
        return redirect('cutless:estadisticas')

def exportar_excel_desperdicio(request):
    """
    Exporta un Excel con el resumen de desperdicio desde estadísticas.
    """
    from django.http import HttpResponse

    try:
        # Obtener todas las optimizaciones del usuario
        todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user)
        
        # Obtener período seleccionado
        periodo = request.GET.get('periodo', 'todos')
        
        # Filtrar por período
        ahora = timezone.now()
        optimizaciones_filtradas = todas_optimizaciones
        
        if periodo == 'semanal':
            fecha_limite = ahora - timedelta(days=7)
            optimizaciones_filtradas = todas_optimizaciones.filter(fecha__gte=fecha_limite)
        elif periodo == 'mensual':
            fecha_limite = ahora - timedelta(days=30)
            optimizaciones_filtradas = todas_optimizaciones.filter(fecha__gte=fecha_limite)
        elif periodo == 'anual':
            fecha_limite = ahora - timedelta(days=365)
            optimizaciones_filtradas = todas_optimizaciones.filter(fecha__gte=fecha_limite)
        
        # Calcular estadísticas
        total_optimizaciones = optimizaciones_filtradas.count()
        
        if total_optimizaciones > 0:
            promedio_aprovechamiento = optimizaciones_filtradas.aggregate(
                avg=Avg('aprovechamiento_total')
            )['avg'] or 0
            max_aprovechamiento = optimizaciones_filtradas.order_by('-aprovechamiento_total').first()
            max_aprovech_val = max_aprovechamiento.aprovechamiento_total if max_aprovechamiento else 0
            min_aprovechamiento = optimizaciones_filtradas.order_by('aprovechamiento_total').first()
            min_aprovech_val = min_aprovechamiento.aprovechamiento_total if min_aprovechamiento else 0
            promedio_desperdicio = 100 - promedio_aprovechamiento
        else:
            promedio_aprovechamiento = 0
            max_aprovech_val = 0
            min_aprovech_val = 0
            promedio_desperdicio = 0
        
        estadisticas = {
            'total_optimizaciones': total_optimizaciones,
            'promedio_aprovechamiento': promedio_aprovechamiento,
            'max_aprovechamiento': max_aprovech_val,
            'min_aprovechamiento': min_aprovech_val,
            'promedio_desperdicio': promedio_desperdicio,
        }
        
        # Generar Excel
        buffer = generar_excel_resumen_desperdicio(optimizaciones_filtradas, estadisticas, periodo)
        
        # Preparar respuesta
        periodo_nombre = {
            'todos': 'todos',
            'semanal': 'semanal',
            'mensual': 'mensual',
            'anual': 'anual'
        }.get(periodo, 'todos')
        
        filename = f"resumen_desperdicio_{periodo_nombre}_{timezone.now().strftime('%Y%m%d')}.xlsx"
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        messages.error(request, f"Error generando Excel: {e}")
        return redirect('cutless:estadisticas')

def estadisticas(request):
    """
    Vista para mostrar estadísticas, gráficos y top de optimizaciones.
    
    IMPORTANTE: Todos los datos están filtrados por usuario (request.user).
    Cada usuario solo ve sus propias optimizaciones y estadísticas.
    """
    # Obtener todas las optimizaciones del usuario actual (filtrado por seguridad)
    todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user).order_by('fecha')
    
    # Obtener período seleccionado
    periodo = request.GET.get('periodo', 'todos')
    
    # Filtrar por período
    ahora = timezone.now()
    optimizaciones_filtradas = todas_optimizaciones
    
    if periodo == 'semanal':
        fecha_limite = ahora - timedelta(days=7)
        optimizaciones_filtradas = todas_optimizaciones.filter(fecha__gte=fecha_limite)
    elif periodo == 'mensual':
        fecha_limite = ahora - timedelta(days=30)
        optimizaciones_filtradas = todas_optimizaciones.filter(fecha__gte=fecha_limite)
    elif periodo == 'anual':
        fecha_limite = ahora - timedelta(days=365)
        optimizaciones_filtradas = todas_optimizaciones.filter(fecha__gte=fecha_limite)
    # 'todos' no necesita filtro
    
    # Calcular estadísticas generales
    total_optimizaciones = optimizaciones_filtradas.count()
    
    if total_optimizaciones > 0:
        # Estadísticas de aprovechamiento
        promedio_aprovechamiento = optimizaciones_filtradas.aggregate(
            avg=Avg('aprovechamiento_total')
        )['avg'] or 0
        
        max_aprovechamiento = optimizaciones_filtradas.order_by('-aprovechamiento_total').first()
        max_aprovech_val = max_aprovechamiento.aprovechamiento_total if max_aprovechamiento else 0
        
        min_aprovechamiento = optimizaciones_filtradas.order_by('aprovechamiento_total').first()
        min_aprovech_val = min_aprovechamiento.aprovechamiento_total if min_aprovechamiento else 0
        
        # Estadísticas de desperdicio (calculado)
        promedio_desperdicio = 100 - promedio_aprovechamiento
        
        # Top 10 optimizaciones (mayor aprovechamiento)
        top_optimizaciones = optimizaciones_filtradas.order_by('-aprovechamiento_total')[:10]
        
        # Generar gráficos (versión normal y alta resolución)
        grafico_aprovechamiento = generar_grafico_aprovechamiento(
            optimizaciones_filtradas.order_by('fecha'), periodo, alta_resolucion=False
        )
        grafico_aprovechamiento_hd = generar_grafico_aprovechamiento(
            optimizaciones_filtradas.order_by('fecha'), periodo, alta_resolucion=True
        )
        grafico_desperdicio = generar_grafico_desperdicio(
            optimizaciones_filtradas.order_by('fecha'), periodo, alta_resolucion=False
        )
        grafico_desperdicio_hd = generar_grafico_desperdicio(
            optimizaciones_filtradas.order_by('fecha'), periodo, alta_resolucion=True
        )
    else:
        promedio_aprovechamiento = 0
        max_aprovech_val = 0
        min_aprovech_val = 0
        promedio_desperdicio = 0
        top_optimizaciones = []
        grafico_aprovechamiento = None
        grafico_aprovechamiento_hd = None
        grafico_desperdicio = None
        grafico_desperdicio_hd = None
    
    # Procesar top optimizaciones para el template
    top_optimizaciones_list = []
    for idx, opt in enumerate(top_optimizaciones, start=1):
        # Parsear piezas
        piezas_procesadas = []
        for linea in opt.piezas.splitlines():
            if linea.strip():
                partes = linea.split(',')
                if len(partes) == 4:
                    piezas_procesadas.append({
                        'nombre': partes[0].strip(),
                        'ancho': partes[1].strip(),
                        'alto': partes[2].strip(),
                        'cantidad': partes[3].strip()
                    })
                elif len(partes) == 3:
                    piezas_procesadas.append({
                        'nombre': 'Pieza',
                        'ancho': partes[0].strip(),
                        'alto': partes[1].strip(),
                        'cantidad': partes[2].strip()
                    })
        
        # Obtener unidad y convertir dimensiones para mostrar
        unidad_opt = getattr(opt, 'unidad_medida', 'cm') or 'cm'
        ancho_mostrar = round(convertir_desde_cm(opt.ancho_tablero, unidad_opt), 2)
        alto_mostrar = round(convertir_desde_cm(opt.alto_tablero, unidad_opt), 2)
        
        top_optimizaciones_list.append({
            'optimizacion': opt,
            'posicion': idx,
            'piezas': piezas_procesadas,
            'ancho_mostrar': ancho_mostrar,
            'alto_mostrar': alto_mostrar,
            'unidad_medida': unidad_opt,
        })
    
    return render(request, 'cutless/estadisticas.html', {
        'total_optimizaciones': total_optimizaciones,
        'promedio_aprovechamiento': round(promedio_aprovechamiento, 2),
        'max_aprovechamiento': round(max_aprovech_val, 2),
        'min_aprovechamiento': round(min_aprovech_val, 2),
        'promedio_desperdicio': round(promedio_desperdicio, 2),
        'top_optimizaciones': top_optimizaciones_list,
        'grafico_aprovechamiento': grafico_aprovechamiento,
        'grafico_aprovechamiento_hd': grafico_aprovechamiento_hd,
        'grafico_desperdicio': grafico_desperdicio,
        'grafico_desperdicio_hd': grafico_desperdicio_hd,
        'periodo': periodo,
        'optimizaciones_filtradas': optimizaciones_filtradas,
    })

def historial_costos(request):
    """
    Vista de historial de costos con gráficos y filtros por fecha.
    Soporta exportación a Excel.
    """
    # Obtener todas las optimizaciones con costos del usuario
    optimizaciones = Optimizacion.objects.filter(usuario=request.user).exclude(
        precio_tablero__isnull=True
    ).order_by('-fecha')
    
    # Filtros por fecha
    fecha_desde = request.GET.get('fecha_desde', '').strip()
    fecha_hasta = request.GET.get('fecha_hasta', '').strip()
    
    if fecha_desde:
        try:
            from datetime import datetime
            fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d')
            optimizaciones = optimizaciones.filter(fecha__gte=fecha_desde_obj)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            from datetime import datetime, timedelta
            fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d') + timedelta(days=1)
            optimizaciones = optimizaciones.filter(fecha__lt=fecha_hasta_obj)
        except ValueError:
            pass
    
    # Calcular estadísticas
    total_optimizaciones = optimizaciones.count()
    costo_total = Decimal('0.00')
    costo_material_total = Decimal('0.00')
    costo_mano_obra_total = Decimal('0.00')
    num_tableros_total = 0
    aprovechamiento_total = Decimal('0.00')
    
    optimizaciones_con_costo = []
    for opt in optimizaciones:
        costo = opt.get_costo_total()
        if costo:
            costo_total += costo
            costo_material = Decimal(str(opt.num_tableros or 0)) * opt.precio_tablero if opt.precio_tablero else Decimal('0.00')
            costo_material_total += costo_material
            costo_mano_obra_total += opt.mano_obra
            num_tableros_total += opt.num_tableros or 0
            aprovechamiento_total += Decimal(str(opt.aprovechamiento_total or 0))
            
            optimizaciones_con_costo.append({
                'optimizacion': opt,
                'costo_total': costo,
                'costo_material': costo_material,
                'costo_mano_obra': opt.mano_obra,
            })
    
    # Calcular estadísticas adicionales
    costo_promedio = costo_total / total_optimizaciones if total_optimizaciones > 0 else Decimal('0.00')
    costo_por_tablero = costo_total / num_tableros_total if num_tableros_total > 0 else Decimal('0.00')
    porcentaje_material = (costo_material_total / costo_total * 100) if costo_total > 0 else Decimal('0.00')
    porcentaje_mano_obra = (costo_mano_obra_total / costo_total * 100) if costo_total > 0 else Decimal('0.00')
    aprovechamiento_promedio = aprovechamiento_total / total_optimizaciones if total_optimizaciones > 0 else Decimal('0.00')
    
    # Verificar si se solicita exportación a Excel
    if request.GET.get('export') == 'excel':
        from django.http import HttpResponse

        estadisticas = {
            'total_optimizaciones': total_optimizaciones,
            'costo_total': float(costo_total),
            'costo_material_total': float(costo_material_total),
            'costo_mano_obra_total': float(costo_mano_obra_total),
            'num_tableros_total': num_tableros_total,
            'costo_promedio': float(costo_promedio),
            'costo_por_tablero': float(costo_por_tablero),
            'porcentaje_material': float(porcentaje_material),
            'porcentaje_mano_obra': float(porcentaje_mano_obra),
            'aprovechamiento_promedio': float(aprovechamiento_promedio),
        }
        
        excel_buffer = generar_excel_historial_costos(
            optimizaciones_con_costo,
            estadisticas,
            fecha_desde=fecha_desde if fecha_desde else None,
            fecha_hasta=fecha_hasta if fecha_hasta else None
        )
        
        # Generar nombre de archivo
        from datetime import datetime
        fecha_actual = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_archivo = f"historial_costos_{fecha_actual}.xlsx"
        
        response = HttpResponse(
            excel_buffer.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        
        return response
    
    # Generar gráfico de costos por fecha
    grafico_costos_base64 = None
    if optimizaciones_con_costo:
        fechas = [opt['optimizacion'].fecha.date() for opt in optimizaciones_con_costo]
        costos = [float(opt['costo_total']) for opt in optimizaciones_con_costo]
        
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from io import BytesIO
        import base64
        
        plt.figure(figsize=(12, 6))
        plt.plot(fechas, costos, marker='o', linestyle='-', linewidth=2, markersize=6)
        plt.title('Evolución de Costos', fontsize=16, fontweight='bold')
        plt.xlabel('Fecha', fontsize=12)
        plt.ylabel('Costo Total ($)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.gcf().autofmt_xdate()
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        grafico_costos_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close()
        buffer.close()
    
    return render(request, 'cutless/historial_costos.html', {
        'optimizaciones_con_costo': optimizaciones_con_costo,
        'total_optimizaciones': total_optimizaciones,
        'costo_total': costo_total,
        'costo_material_total': costo_material_total,
        'costo_mano_obra_total': costo_mano_obra_total,
        'num_tableros_total': num_tableros_total,
        'costo_promedio': costo_promedio,
        'costo_por_tablero': costo_por_tablero,
        'porcentaje_material': porcentaje_material,
        'porcentaje_mano_obra': porcentaje_mano_obra,
        'aprovechamiento_promedio': aprovechamiento_promedio,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'grafico_costos_base64': grafico_costos_base64,
    })

def comparar_optimizaciones(request):
    """
    Vista para seleccionar y comparar dos optimizaciones lado a lado.
    """
    optimizaciones = Optimizacion.objects.filter(usuario=request.user).order_by('-fecha')
    
    # Si se seleccionaron dos optimizaciones para comparar
    opt1_id = request.GET.get('opt1')
    opt2_id = request.GET.get('opt2')
    
    optimizacion1 = None
    optimizacion2 = None
    
    # Calcular diferencias y desperdicios
    diferencia_aprovechamiento = None
    diferencia_tableros = None
    diferencia_desperdicio = None
    desperdicio1 = None
    desperdicio2 = None
    
    if opt1_id and opt2_id:
        try:
            optimizacion1 = Optimizacion.objects.get(pk=opt1_id, usuario=request.user)
            optimizacion2 = Optimizacion.objects.get(pk=opt2_id, usuario=request.user)
            
            # Calcular num_tableros si no está guardado (para optimizaciones antiguas)
            def obtener_num_tableros(optimizacion):
                """Obtiene el número de tableros, calculándolo si no está guardado"""
                if optimizacion.num_tableros and optimizacion.num_tableros > 0:
                    return optimizacion.num_tableros
                
                # Si no está guardado, calcularlo desde las piezas (tuplas ancho×alto×cantidad en cm)
                try:
                    piezas_para_grafico = []
                    unidad = getattr(optimizacion, 'unidad_medida', 'cm') or 'cm'
                    for linea in optimizacion.piezas.splitlines():
                        if linea.strip():
                            partes = linea.split(',')
                            if len(partes) >= 3:
                                cantidad = int(partes[-1]) if len(partes) >= 4 else int(partes[2])
                                ancho_idx = 1 if len(partes) >= 4 else 0
                                alto_idx = 2 if len(partes) >= 4 else 1
                                ancho = float(partes[ancho_idx])
                                alto = float(partes[alto_idx])
                                piezas_para_grafico.append((
                                    convertir_a_cm(ancho, unidad),
                                    convertir_a_cm(alto, unidad),
                                    cantidad,
                                ))

                    if piezas_para_grafico:
                        margen = getattr(optimizacion, 'margen_corte', 0.3) or 0.3
                        permitir_rot = getattr(optimizacion, 'permitir_rotacion', True)
                        imagenes_calc, _, _ = generar_grafico(
                            piezas_para_grafico,
                            optimizacion.ancho_tablero,
                            optimizacion.alto_tablero,
                            unidad='cm',
                            permitir_rotacion=permitir_rot,
                            margen_corte=margen
                        )
                        return len(imagenes_calc)
                except Exception:
                    pass
                
                # Fallback: estimar desde el área
                try:
                    area_tablero = optimizacion.ancho_tablero * optimizacion.alto_tablero
                    area_total = 0
                    for linea in optimizacion.piezas.splitlines():
                        if linea.strip():
                            partes = linea.split(',')
                            if len(partes) >= 3:
                                cantidad = int(partes[-1]) if len(partes) >= 4 else int(partes[2])
                                ancho_idx = 1 if len(partes) >= 4 else 0
                                alto_idx = 2 if len(partes) >= 4 else 1
                                ancho = float(partes[ancho_idx])
                                alto = float(partes[alto_idx])
                                unidad = getattr(optimizacion, 'unidad_medida', 'cm') or 'cm'
                                ancho_cm = convertir_a_cm(ancho, unidad)
                                alto_cm = convertir_a_cm(alto, unidad)
                                area_total += (ancho_cm * alto_cm) * cantidad
                    if area_tablero > 0:
                        return max(1, int(area_total / area_tablero) + 1)
                except Exception:
                    pass
                
                return 1  # Valor por defecto
            
            num_tableros1 = obtener_num_tableros(optimizacion1)
            num_tableros2 = obtener_num_tableros(optimizacion2)
            
            # Actualizar num_tableros si estaba en 0 (para guardarlo en la BD)
            if optimizacion1.num_tableros == 0 and num_tableros1 > 0:
                optimizacion1.num_tableros = num_tableros1
                optimizacion1.save(update_fields=['num_tableros'])
            if optimizacion2.num_tableros == 0 and num_tableros2 > 0:
                optimizacion2.num_tableros = num_tableros2
                optimizacion2.save(update_fields=['num_tableros'])
            
            # Calcular diferencias
            diferencia_aprovechamiento = optimizacion2.aprovechamiento_total - optimizacion1.aprovechamiento_total
            diferencia_tableros = num_tableros2 - num_tableros1
            
            # Calcular desperdicios (100% - aprovechamiento)
            desperdicio1 = 100 - optimizacion1.aprovechamiento_total
            desperdicio2 = 100 - optimizacion2.aprovechamiento_total
            diferencia_desperdicio = desperdicio2 - desperdicio1
            
        except Optimizacion.DoesNotExist:
            messages.error(request, "Una o ambas optimizaciones no fueron encontradas.")
            return redirect('cutless:comparar_optimizaciones')
    
    return render(request, 'cutless/comparar_optimizaciones.html', {
        'optimizaciones': optimizaciones,
        'optimizacion1': optimizacion1,
        'optimizacion2': optimizacion2,
        'diferencia_aprovechamiento': diferencia_aprovechamiento,
        'diferencia_tableros': diferencia_tableros,
        'diferencia_desperdicio': diferencia_desperdicio,
        'desperdicio1': desperdicio1,
        'desperdicio2': desperdicio2,
    })

