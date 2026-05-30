from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from ..models import Optimizacion
from ..utils import convertir_desde_cm


def borrar_seleccion(request):
    if request.method == "POST":
        seleccion = request.POST.getlist('seleccion')
        if not seleccion:
            messages.warning(request, "No se seleccionó ninguna optimización para borrar.")
            return redirect('cutless:historial')

        optimizaciones = Optimizacion.objects.filter(id__in=seleccion, usuario=request.user)
        count = optimizaciones.count()
        optimizaciones.delete()

        if count > 0:
            messages.success(request, f"Se eliminaron {count} optimizaciones seleccionadas del historial.")
        else:
            messages.warning(request, "No se encontraron optimizaciones válidas para eliminar.")

        return redirect('cutless:historial')
    else:
        messages.error(request, "Operación no permitida.")
        return redirect('cutless:historial')

def borrar_historial(request):
    if request.method == "POST":
        optimizaciones = Optimizacion.objects.filter(usuario=request.user)
        count = optimizaciones.count()
        optimizaciones.delete()
        messages.success(request, f"Se eliminaron {count} optimizaciones del historial.")
        return redirect('cutless:historial')
    else:
        messages.error(request, "Operación no permitida.")
        return redirect('cutless:historial')

def historial(request):
    # Obtener TODAS las optimizaciones del usuario para calcular números absolutos
    todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user)
    total_absoluto = todas_optimizaciones.count()
    
    # Ordenamiento (aplicar a todas para calcular números correctos)
    ordenar_por = request.GET.get('ordenar_por', 'fecha_desc')
    
    if ordenar_por == 'fecha_desc':
        todas_optimizaciones = todas_optimizaciones.order_by('-fecha')
    elif ordenar_por == 'fecha_asc':
        todas_optimizaciones = todas_optimizaciones.order_by('fecha')
    elif ordenar_por == 'aprovechamiento_desc':
        todas_optimizaciones = todas_optimizaciones.order_by('-aprovechamiento_total')
    elif ordenar_por == 'aprovechamiento_asc':
        todas_optimizaciones = todas_optimizaciones.order_by('aprovechamiento_total')
    else:
        todas_optimizaciones = todas_optimizaciones.order_by('-fecha')
    
    # Determinar si el ordenamiento es descendente o ascendente
    es_descendente = ordenar_por in ['fecha_desc', 'aprovechamiento_desc']
    
    # Crear diccionario de ID -> número absoluto
    numeros_absolutos = {}
    for idx, opt in enumerate(todas_optimizaciones, start=1):
        if es_descendente:
            numeros_absolutos[opt.id] = total_absoluto - idx + 1
        else:
            numeros_absolutos[opt.id] = idx
    
    # Ahora aplicar filtros para mostrar
    optimizaciones = todas_optimizaciones
    
    # Filtro por favoritos
    solo_favoritos = request.GET.get('solo_favoritos', '').strip()
    if solo_favoritos == 'true':
        optimizaciones = optimizaciones.filter(favorito=True)
    
    # Filtro por nombre de pieza
    nombre_pieza = request.GET.get('nombre_pieza', '').strip()
    if nombre_pieza:
        # Buscar en el campo piezas que contiene el nombre
        optimizaciones = optimizaciones.filter(piezas__icontains=nombre_pieza)
    
    # Filtro por fecha
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
    
    # PAGINACIÓN
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    page = request.GET.get('page', 1)
    paginator = Paginator(optimizaciones, 12)  # 12 optimizaciones por página
    try:
        optimizaciones_page = paginator.page(page)
    except PageNotAnInteger:
        optimizaciones_page = paginator.page(1)
    except EmptyPage:
        optimizaciones_page = paginator.page(paginator.num_pages)

    optimizaciones_con_piezas = []
    for opt in optimizaciones_page:
        numero_mostrado = numeros_absolutos.get(opt.id, 0)
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
        unidad_opt = getattr(opt, 'unidad_medida', 'cm') or 'cm'
        ancho_mostrar = round(convertir_desde_cm(opt.ancho_tablero, unidad_opt), 2)
        alto_mostrar = round(convertir_desde_cm(opt.alto_tablero, unidad_opt), 2)
        optimizaciones_con_piezas.append({
            'optimizacion': opt,
            'piezas': piezas_procesadas,
            'numero': numero_mostrado,
            'ancho_mostrar': ancho_mostrar,
            'alto_mostrar': alto_mostrar,
            'unidad_medida': unidad_opt,
        })

    return render(request, 'cutless/historial.html', {
        'optimizaciones_con_piezas': optimizaciones_con_piezas,
        'nombre_pieza': nombre_pieza,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'ordenar_por': ordenar_por,
        'solo_favoritos': solo_favoritos,
        'total_sin_filtro': total_absoluto,
        'page_obj': optimizaciones_page,
        'paginator': paginator,
    })

def borrar_optimizacion(request, pk):
    """
    Elimina una optimización individual del usuario actual.
    """
    optimizacion = get_object_or_404(Optimizacion, pk=pk, usuario=request.user)
    todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user).order_by('-fecha')
    total_absoluto = todas_optimizaciones.count()
    numero_mostrado = None
    for idx, opt in enumerate(todas_optimizaciones, start=1):
        if opt.id == pk:
            numero_mostrado = total_absoluto - idx + 1
            break
    if numero_mostrado is None:
        numero_mostrado = pk

    if request.method == "POST":
        optimizacion.delete()
        messages.success(request, f"Optimización #{numero_mostrado} eliminada correctamente.")
        return redirect('cutless:historial')
    else:
        return render(request, 'cutless/eliminar_optimizacion.html', {
            'optimizacion': optimizacion,
            'numero_mostrado': numero_mostrado,
        })

def toggle_favorito(request, pk):
    """
    Marca o desmarca una optimización como favorita.
    Soporta tanto peticiones AJAX como peticiones normales.
    """
    optimizacion = get_object_or_404(Optimizacion, pk=pk, usuario=request.user)
    optimizacion.favorito = not optimizacion.favorito
    optimizacion.save()
    
    # Si es una petición AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax') == 'true':
        from django.http import JsonResponse
        return JsonResponse({
            'success': True,
            'favorito': optimizacion.favorito,
            'message': f"⭐ Optimización #{pk} marcada como favorita." if optimizacion.favorito else f"Optimización #{pk} eliminada de favoritos."
        })
    
    # Si no es AJAX, comportamiento normal con mensajes
    if optimizacion.favorito:
        messages.success(request, f"⭐ Optimización #{pk} marcada como favorita.")
    else:
        messages.info(request, f"Optimización #{pk} eliminada de favoritos.")
    
    # Redirigir de vuelta a historial, manteniendo los filtros (solo si no es AJAX)
    return redirect(request.META.get('HTTP_REFERER', 'cutless:historial'))

