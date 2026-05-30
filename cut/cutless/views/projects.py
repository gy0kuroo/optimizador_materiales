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
    persistir_resultado_optimizacion,
    obtener_resultado_optimizacion,
    preparar_contexto_resultado,
    pdf_path_para_template,
    respuesta_png_tablero,
    respuesta_pdf_optimizacion,
)
from .common import _materiales_data_json_index, requiere_permiso
def crear_proyecto(request):
    """
    Crea un nuevo proyecto con opción de agregar optimizaciones.
    """
    if request.method == "POST":
        form = ProyectoForm(request.POST, user=request.user)
        if form.is_valid():
            proyecto = form.save(commit=False)
            proyecto.usuario = request.user
            proyecto.save()
            
            # Asignar optimizaciones seleccionadas al proyecto
            optimizaciones_seleccionadas = form.cleaned_data.get('optimizaciones', [])
            if optimizaciones_seleccionadas:
                # Obtener IDs de las optimizaciones seleccionadas
                optimizaciones_ids = [opt.pk for opt in optimizaciones_seleccionadas]
                # Verificar que las optimizaciones pertenezcan al usuario y asignarlas
                optimizaciones_validas = Optimizacion.objects.filter(
                    pk__in=optimizaciones_ids,
                    usuario=request.user
                )
                optimizaciones_validas.update(proyecto=proyecto)
                num_optimizaciones = optimizaciones_validas.count()
                mensaje_proyecto = f'Se ha creado el proyecto "{proyecto.nombre}" exitosamente con {num_optimizaciones} optimización(es) asociada(s).'
            else:
                mensaje_proyecto = f'Se ha creado el proyecto "{proyecto.nombre}" exitosamente.'
            
            # Enviar notificación de proyecto creado (esto mostrará el mensaje según la configuración)
            enviar_notificacion(
                request,
                'proyecto_creado',
                'Proyecto Creado',
                mensaje_proyecto,
                {'proyecto_id': proyecto.id, 'nombre': proyecto.nombre}
            )
            
            return redirect('cutless:detalle_proyecto', pk=proyecto.pk)
    else:
        form = ProyectoForm(user=request.user)
    
    # Preparar información adicional de optimizaciones para el template
    optimizaciones_info = []
    optimizaciones_seleccionadas_ids = []
    
    if form.fields['optimizaciones'].queryset:
        todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user).order_by('-fecha')
        total_optimizaciones = todas_optimizaciones.count()
        
        for opt in form.fields['optimizaciones'].queryset:
            # Calcular número de lista
            numero_lista = opt.pk
            for idx, optimizacion_lista in enumerate(todas_optimizaciones, start=1):
                if optimizacion_lista.id == opt.id:
                    numero_lista = total_optimizaciones - idx + 1
                    break
            
            # Extraer nombres de piezas
            nombres_piezas = []
            if opt.piezas:
                for linea in opt.piezas.splitlines():
                    if linea.strip():
                        partes = linea.split(',')
                        if len(partes) == 4:  # Formato con nombre: nombre,ancho,alto,cantidad
                            nombre = partes[0].strip()
                            cantidad = int(partes[3].strip())
                            nombres_piezas.append(f"{nombre} (x{cantidad})")
                        elif len(partes) == 3:  # Formato sin nombre: ancho,alto,cantidad
                            cantidad = int(partes[2].strip())
                            nombres_piezas.append(f"Pieza (x{cantidad})")
            
            optimizaciones_info.append({
                'optimizacion': opt,
                'numero_lista': numero_lista,
                'seleccionada': opt.pk in optimizaciones_seleccionadas_ids,
                'nombres_piezas': nombres_piezas[:5],  # Máximo 5 piezas para no hacer muy largo
                'total_piezas': len(nombres_piezas),
            })
    
    return render(request, 'cutless/crear_proyecto.html', {
        'form': form,
        'optimizaciones_info': optimizaciones_info,
    })

def eliminar_proyecto(request, pk):
    """
    Elimina un proyecto.
    """
    try:
        proyecto = Proyecto.objects.get(pk=pk, usuario=request.user)
    except Proyecto.DoesNotExist:
        messages.error(request, "No se encontró el proyecto.")
        return redirect('cutless:lista_proyectos')
    
    optimizaciones_count = proyecto.get_total_optimizaciones()
    
    if request.method == "POST":
        accion = request.POST.get('accion', 'mover')
        
        if accion == 'eliminar':
            # Eliminar todas las optimizaciones del proyecto
            proyecto.optimizacion_set.all().delete()
        # Si es 'mover', las optimizaciones simplemente perderán la referencia al proyecto (SET_NULL)
        
        nombre = proyecto.nombre
        proyecto.delete()
        messages.success(request, f'✅ Proyecto "{nombre}" eliminado exitosamente.')
        return redirect('cutless:lista_proyectos')
    
    return render(request, 'cutless/eliminar_proyecto.html', {
        'proyecto': proyecto,
        'optimizaciones_count': optimizaciones_count,
    })

def agregar_optimizaciones_proyecto(request, pk):
    """
    Permite agregar múltiples optimizaciones a un proyecto existente.
    """
    proyecto = get_object_or_404(Proyecto, pk=pk, usuario=request.user)
    
    # Obtener optimizaciones que aún no están en el proyecto
    optimizaciones_en_proyecto = proyecto.optimizacion_set.values_list('pk', flat=True)
    optimizaciones_disponibles = Optimizacion.objects.filter(
        usuario=request.user
    ).exclude(pk__in=optimizaciones_en_proyecto).order_by('-fecha')
    
    if request.method == "POST":
        optimizaciones_ids = request.POST.getlist('optimizaciones')
        if optimizaciones_ids:
            optimizaciones_seleccionadas = Optimizacion.objects.filter(
                pk__in=optimizaciones_ids,
                usuario=request.user
            )
            # Asignar el proyecto a las optimizaciones seleccionadas
            optimizaciones_seleccionadas.update(proyecto=proyecto)
            
            messages.success(
                request, 
                f'✅ {optimizaciones_seleccionadas.count()} optimización(es) agregada(s) al proyecto "{proyecto.nombre}".'
            )
            return redirect('cutless:detalle_proyecto', pk=proyecto.pk)
        else:
            messages.warning(request, "Debes seleccionar al menos una optimización.")
    
    return render(request, 'cutless/agregar_optimizaciones_proyecto.html', {
        'proyecto': proyecto,
        'optimizaciones_disponibles': optimizaciones_disponibles,
    })

def lista_proyectos(request):
    """
    Lista todos los proyectos del usuario con filtros y búsqueda.
    """
    proyectos = Proyecto.objects.filter(usuario=request.user).select_related('cliente').order_by('-fecha_creacion')
    
    # Filtros
    estado_filtro = request.GET.get('estado', '')
    if estado_filtro:
        proyectos = proyectos.filter(estado=estado_filtro)
    
    # Búsqueda
    busqueda = request.GET.get('busqueda', '').strip()
    if busqueda:
        proyectos = proyectos.filter(
            Q(nombre__icontains=busqueda) |
            Q(descripcion__icontains=busqueda) |
            Q(cliente__nombre__icontains=busqueda)
        )
    
    return render(request, 'cutless/lista_proyectos.html', {
        'proyectos': proyectos,
        'estado_filtro': estado_filtro,
        'busqueda': busqueda,
    })

def detalle_proyecto(request, pk):
    """
    Muestra el detalle de un proyecto con sus optimizaciones y métricas.
    """
    try:
        proyecto = Proyecto.objects.select_related('cliente').get(
            pk=pk,
            usuario=request.user
        )
    except Proyecto.DoesNotExist:
        messages.error(request, "Proyecto no encontrado.")
        return redirect('cutless:lista_proyectos')
    
    # Optimizaciones del proyecto
    optimizaciones = Optimizacion.objects.filter(proyecto=proyecto, usuario=request.user).order_by('-fecha')
    
    # Estadísticas
    total_optimizaciones = optimizaciones.count()
    costo_total = proyecto.get_total_costo()
    
    # Calcular promedio de aprovechamiento
    aprovechamiento_promedio = optimizaciones.aggregate(
        promedio=Avg('aprovechamiento_total')
    )['promedio'] or 0
    
    # Total de tableros
    total_tableros = sum(opt.num_tableros or 0 for opt in optimizaciones)
    
    return render(request, 'cutless/detalle_proyecto.html', {
        'proyecto': proyecto,
        'optimizaciones': optimizaciones,
        'total_optimizaciones': total_optimizaciones,
        'costo_total': costo_total,
        'aprovechamiento_promedio': aprovechamiento_promedio,
        'total_tableros': total_tableros,
    })

def editar_proyecto(request, pk):
    """
    Edita un proyecto existente.
    """
    proyecto = get_object_or_404(Proyecto, pk=pk, usuario=request.user)
    
    if request.method == "POST":
        form = ProyectoForm(request.POST, instance=proyecto, user=request.user)
        if form.is_valid():
            proyecto = form.save(commit=False)
            proyecto.save()
            
            # Actualizar optimizaciones seleccionadas
            optimizaciones_seleccionadas = form.cleaned_data.get('optimizaciones', [])
            optimizaciones_seleccionadas_ids = [opt.pk for opt in optimizaciones_seleccionadas]
            
            # Primero, quitar el proyecto de todas las optimizaciones que ya no están seleccionadas
            optimizaciones_actuales = proyecto.optimizacion_set.all()
            for opt in optimizaciones_actuales:
                if opt.pk not in optimizaciones_seleccionadas_ids:
                    opt.proyecto = None
                    opt.save()
            
            # Luego, asignar el proyecto a las optimizaciones seleccionadas
            if optimizaciones_seleccionadas_ids:
                Optimizacion.objects.filter(
                    pk__in=optimizaciones_seleccionadas_ids,
                    usuario=request.user
                ).update(proyecto=proyecto)
            
            messages.success(request, f'✅ Proyecto "{proyecto.nombre}" actualizado exitosamente.')
            return redirect('cutless:detalle_proyecto', pk=proyecto.pk)
    else:
        form = ProyectoForm(instance=proyecto, user=request.user)
    
    # Preparar información adicional de optimizaciones para el template
    optimizaciones_info = []
    optimizaciones_seleccionadas_ids = list(proyecto.optimizacion_set.values_list('pk', flat=True))
    
    if form.fields['optimizaciones'].queryset:
        todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user).order_by('-fecha')
        total_optimizaciones = todas_optimizaciones.count()
        
        for opt in form.fields['optimizaciones'].queryset:
            # Calcular número de lista
            numero_lista = opt.pk
            for idx, optimizacion_lista in enumerate(todas_optimizaciones, start=1):
                if optimizacion_lista.id == opt.id:
                    numero_lista = total_optimizaciones - idx + 1
                    break
            
            # Extraer nombres de piezas
            nombres_piezas = []
            if opt.piezas:
                for linea in opt.piezas.splitlines():
                    if linea.strip():
                        partes = linea.split(',')
                        if len(partes) == 4:  # Formato con nombre: nombre,ancho,alto,cantidad
                            nombre = partes[0].strip()
                            cantidad = int(partes[3].strip())
                            nombres_piezas.append(f"{nombre} (x{cantidad})")
                        elif len(partes) == 3:  # Formato sin nombre: ancho,alto,cantidad
                            cantidad = int(partes[2].strip())
                            nombres_piezas.append(f"Pieza (x{cantidad})")
            
            optimizaciones_info.append({
                'optimizacion': opt,
                'numero_lista': numero_lista,
                'seleccionada': opt.pk in optimizaciones_seleccionadas_ids,
                'nombres_piezas': nombres_piezas[:5],  # Máximo 5 piezas para no hacer muy largo
                'total_piezas': len(nombres_piezas),
            })
    
    return render(request, 'cutless/editar_proyecto.html', {
        'form': form,
        'proyecto': proyecto,
        'optimizaciones_info': optimizaciones_info,
    })

