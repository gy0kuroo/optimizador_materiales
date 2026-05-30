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
def lista_materiales(request):
    """
    Lista todos los materiales del usuario y los predefinidos del sistema.
    """
    # Materiales del usuario
    materiales_usuario = Material.objects.filter(usuario=request.user)
    
    # Materiales predefinidos del sistema
    materiales_sistema = Material.objects.filter(es_predefinido=True)
    
    # Búsqueda
    busqueda = request.GET.get('busqueda', '').strip()
    if busqueda:
        materiales_usuario = materiales_usuario.filter(nombre__icontains=busqueda)
        materiales_sistema = materiales_sistema.filter(nombre__icontains=busqueda)
    
    return render(request, 'cutless/lista_materiales.html', {
        'materiales_usuario': materiales_usuario,
        'materiales_sistema': materiales_sistema,
        'busqueda': busqueda,
    })

def crear_material(request):
    """
    Crea un nuevo material.
    """
    if request.method == "POST":
        form = MaterialForm(request.POST)
        if form.is_valid():
            material = form.save(commit=False)
            material.usuario = request.user
            material.es_predefinido = False  # Solo admin puede crear predefinidos
            material.save()
            messages.success(request, f'✅ Material "{material.nombre}" creado exitosamente.')
            return redirect('cutless:lista_materiales')
    else:
        form = MaterialForm()
    
    return render(request, 'cutless/crear_material.html', {
        'form': form,
    })

def eliminar_material(request, pk):
    """
    Elimina un material (incluyendo predefinidos).
    """
        # Permitir eliminar materiales predefinidos también
    material = get_object_or_404(
        Material,
        Q(pk=pk, usuario=request.user) | Q(pk=pk, es_predefinido=True)
    )
    
    # Verificar que no esté en uso
    optimizaciones_usando = Optimizacion.objects.filter(material=material).count()
    if optimizaciones_usando > 0:
        messages.warning(
            request, 
            f'⚠️ No se puede eliminar el material "{material.nombre}" porque está siendo usado en {optimizaciones_usando} optimización(es).'
        )
        return redirect('cutless:lista_materiales')
    
    if request.method == "POST":
        nombre = material.nombre
        es_predefinido = material.es_predefinido
        material.delete()
        tipo = "predefinido" if es_predefinido else "personal"
        messages.success(request, f'✅ Material {tipo} "{nombre}" eliminado exitosamente.')
        return redirect('cutless:lista_materiales')
    
    return render(request, 'cutless/eliminar_material.html', {
        'material': material,
    })

def editar_material(request, pk):
    """
    Edita un material existente.
    Permite editar materiales del usuario y materiales predefinidos del sistema.
    """
    # Permitir editar materiales del usuario o predefinidos
    material = get_object_or_404(Material, pk=pk)
    
    # Verificar permisos: solo puede editar si es suyo o es predefinido
    if not material.es_predefinido and material.usuario != request.user:
        messages.error(request, "No tienes permiso para editar este material.")
        return redirect('cutless:lista_materiales')
    
    if request.method == "POST":
        form = MaterialForm(request.POST, instance=material)
        if form.is_valid():
            material_actualizado = form.save(commit=False)
            # Si es predefinido, asegurar que siga siendo predefinido
            if material.es_predefinido:
                material_actualizado.es_predefinido = True
                material_actualizado.usuario = None
            material_actualizado.save()
            messages.success(request, f'✅ Material "{material_actualizado.nombre}" actualizado exitosamente.')
            return redirect('cutless:lista_materiales')
    else:
        form = MaterialForm(instance=material)
    
    return render(request, 'cutless/editar_material.html', {
        'form': form,
        'material': material,
    })

