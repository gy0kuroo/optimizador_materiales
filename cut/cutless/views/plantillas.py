from django.contrib import messages
from django.db.models import Q
from django.forms import formset_factory
from django.shortcuts import render, redirect, get_object_or_404

from ..forms import PlantillaForm, TableroForm, PiezaForm
from ..models import Plantilla, Optimizacion, Material
from ..utils import convertir_desde_cm


def editar_plantilla(request, pk):
    """
    Edita una plantilla existente.
    """
    plantilla = get_object_or_404(Plantilla, pk=pk)
    
    # Verificar permisos: solo puede editar si es suya o es predefinida
    if not plantilla.es_predefinida and plantilla.usuario != request.user:
        messages.error(request, "No tienes permiso para editar esta plantilla.")
        return redirect('cutless:lista_plantillas')
    
    copiar_sistema = plantilla.es_predefinida
    if request.method == "POST":
        form = PlantillaForm(request.POST, instance=plantilla, user=request.user)
        if form.is_valid():
            plantilla_actualizada = form.save(commit=False)
            if copiar_sistema:
                plantilla_actualizada.pk = None
                plantilla_actualizada.es_predefinida = False
                plantilla_actualizada.usuario = request.user
            plantilla_actualizada.save()
            accion = 'copiada a tus plantillas' if copiar_sistema else 'actualizada'
            messages.success(request, f'Plantilla "{plantilla_actualizada.nombre}" {accion}.')
            return redirect('cutless:lista_plantillas')
    else:
        form = PlantillaForm(instance=plantilla, user=request.user)
    
    return render(request, 'cutless/editar_plantilla.html', {
        'form': form,
        'plantilla': plantilla,
    })

def crear_plantilla(request):
    """
    Crea una nueva plantilla desde una optimización o desde cero.
    """
    # Si viene desde una optimización específica
    optimizacion_id = request.GET.get('optimizacion')
    optimizacion = None
    if optimizacion_id:
        optimizacion = get_object_or_404(Optimizacion, pk=optimizacion_id, usuario=request.user)
    
    if request.method == "POST":
        form = PlantillaForm(request.POST, user=request.user)
        if form.is_valid():
            plantilla = form.save(commit=False)
            plantilla.usuario = request.user
            plantilla.es_predefinida = False
            plantilla.save()
            messages.success(request, f'✅ Plantilla "{plantilla.nombre}" creada exitosamente.')
            return redirect('cutless:lista_plantillas')
    else:
        form = PlantillaForm(user=request.user)
        if optimizacion:
            # Prellenar datos desde la optimización
            unidad_opt = getattr(optimizacion, 'unidad_medida', 'cm') or 'cm'
            ancho_mostrar = convertir_desde_cm(optimizacion.ancho_tablero, unidad_opt)
            alto_mostrar = convertir_desde_cm(optimizacion.alto_tablero, unidad_opt)
            margen_mm = round(getattr(optimizacion, 'margen_corte', 0.3) * 10, 1)
            
            form.initial['nombre'] = f"Plantilla de {optimizacion.fecha.strftime('%d/%m/%Y')}"
            form.initial['ancho_tablero'] = ancho_mostrar
            form.initial['alto_tablero'] = alto_mostrar
            form.initial['unidad_medida'] = unidad_opt
            form.initial['piezas'] = optimizacion.piezas
            form.initial['permitir_rotacion'] = optimizacion.permitir_rotacion
            form.initial['margen_corte'] = margen_mm
    
    return render(request, 'cutless/crear_plantilla.html', {
        'form': form,
        'optimizacion': optimizacion,
    })

def lista_plantillas(request):
    """
    Lista todas las plantillas del usuario y las predefinidas del sistema.
    """
    # Plantillas del usuario
    plantillas_usuario = Plantilla.objects.filter(usuario=request.user, es_predefinida=False)
    
    # Plantillas predefinidas del sistema
    plantillas_sistema = Plantilla.objects.filter(es_predefinida=True)
    
    # Búsqueda
    busqueda = request.GET.get('busqueda', '').strip()
    categoria_filtro = request.GET.get('categoria', '')
    
    if busqueda:
        plantillas_usuario = plantillas_usuario.filter(nombre__icontains=busqueda)
        plantillas_sistema = plantillas_sistema.filter(nombre__icontains=busqueda)
    
    if categoria_filtro:
        plantillas_usuario = plantillas_usuario.filter(categoria=categoria_filtro)
        plantillas_sistema = plantillas_sistema.filter(categoria=categoria_filtro)
    
    return render(request, 'cutless/lista_plantillas.html', {
        'plantillas_usuario': plantillas_usuario,
        'plantillas_sistema': plantillas_sistema,
        'busqueda': busqueda,
        'categoria_filtro': categoria_filtro,
    })

def eliminar_plantilla(request, pk):
    """
    Elimina una plantilla.
    """
    plantilla = get_object_or_404(Plantilla, pk=pk, usuario=request.user, es_predefinida=False)
    
    if request.method == "POST":
        nombre = plantilla.nombre
        plantilla.delete()
        messages.success(request, f'✅ Plantilla "{nombre}" eliminada exitosamente.')
        return redirect('cutless:lista_plantillas')
    
    return render(request, 'cutless/eliminar_plantilla.html', {
        'plantilla': plantilla,
    })

def usar_plantilla(request, pk):
    """
    Carga una plantilla en el formulario de optimización.
    """
    plantilla = get_object_or_404(Plantilla, pk=pk)
    
    # Verificar permisos: solo puede usar si es suya o es predefinida
    if not plantilla.es_predefinida and plantilla.usuario != request.user:
        messages.error(request, "No tienes permiso para usar esta plantilla.")
        return redirect('cutless:lista_plantillas')
    
    # Convertir dimensiones a la unidad de la plantilla
    unidad = plantilla.unidad_medida
    ancho_mostrar = convertir_desde_cm(plantilla.ancho_tablero, unidad)
    alto_mostrar = convertir_desde_cm(plantilla.alto_tablero, unidad)
    margen_mm = round(plantilla.margen_corte * 10, 1)
    
    # Preparar formulario con datos de la plantilla
    from django.forms import formset_factory
    PiezaFormSet = formset_factory(PiezaForm, extra=0, max_num=20)
    
    piezas_data = plantilla.get_piezas_list()
    pieza_formset = PiezaFormSet(initial=piezas_data)
    
    tablero_form = TableroForm(user=request.user, initial={
        'ancho': ancho_mostrar,
        'alto': alto_mostrar,
        'unidad_medida': unidad,
        'permitir_rotacion': plantilla.permitir_rotacion,
        'margen_corte': margen_mm,
    })
    
    # Preparar datos de materiales para JavaScript
    materiales_data = {}
    for material in Material.objects.filter(
        Q(usuario=request.user) | Q(es_predefinido=True)
    ):
        materiales_data[str(material.pk)] = {
            'precio': float(material.precio) if material.precio else None,
            'nombre': material.nombre
        }
    
    messages.info(request, f'📋 Plantilla "{plantilla.nombre}" cargada. Completa los datos y genera la optimización.')
    
    return render(request, 'cutless/index.html', {
        'tablero_form': tablero_form,
        'pieza_formset': pieza_formset,
        'materiales_data': materiales_data,
        'plantilla_cargada': plantilla,
    })

