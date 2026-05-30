from decimal import Decimal

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from ..forms import ClienteForm
from ..models import Cliente, Optimizacion, Proyecto


def historial_cliente(request, pk):
    """
    Muestra el historial de optimizaciones y proyectos de un cliente.
    """
    cliente = get_object_or_404(Cliente, pk=pk, usuario=request.user)
    
    # Optimizaciones del cliente
    optimizaciones = Optimizacion.objects.filter(cliente=cliente, usuario=request.user).order_by('-fecha')
    
    # Proyectos del cliente
    proyectos = Proyecto.objects.filter(cliente=cliente, usuario=request.user).order_by('-fecha_creacion')
    
    # Estadísticas
    total_optimizaciones = optimizaciones.count()
    total_proyectos = proyectos.count()
    
    # Calcular costo total
    costo_total = Decimal('0.00')
    for opt in optimizaciones:
        costo = opt.get_costo_total()
        if costo:
            costo_total += costo
    
    return render(request, 'cutless/historial_cliente.html', {
        'cliente': cliente,
        'optimizaciones': optimizaciones,
        'proyectos': proyectos,
        'total_optimizaciones': total_optimizaciones,
        'total_proyectos': total_proyectos,
        'costo_total': costo_total,
    })

def lista_clientes(request):
    """
    Lista todos los clientes del usuario con búsqueda.
    """
    clientes = Cliente.objects.filter(usuario=request.user)
    
    # Búsqueda
    busqueda = request.GET.get('busqueda', '').strip()
    if busqueda:
        clientes = clientes.filter(
            Q(nombre__icontains=busqueda) |
            Q(rut__icontains=busqueda) |
            Q(email__icontains=busqueda)
        )
    
    # Estadísticas
    total_clientes = clientes.count()
    
    return render(request, 'cutless/lista_clientes.html', {
        'clientes': clientes,
        'busqueda': busqueda,
        'total_clientes': total_clientes,
    })

def editar_cliente(request, pk):
    """
    Edita un cliente existente.
    """
    try:
        cliente = Cliente.objects.get(pk=pk, usuario=request.user)
    except Cliente.DoesNotExist:
        messages.error(request, "No se encontró el cliente o no tienes permiso para editarlo.")
        return redirect('cutless:lista_clientes')
    
    if request.method == "POST":
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ Cliente "{cliente.nombre}" actualizado exitosamente.')
            return redirect('cutless:lista_clientes')
    else:
        form = ClienteForm(instance=cliente)
    
    return render(request, 'cutless/editar_cliente.html', {
        'form': form,
        'cliente': cliente,
    })

def crear_cliente(request):
    """
    Crea un nuevo cliente.
    """
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.usuario = request.user
            cliente.save()
            messages.success(request, f'✅ Cliente "{cliente.nombre}" creado exitosamente.')
            return redirect('cutless:lista_clientes')
    else:
        form = ClienteForm()
    
    return render(request, 'cutless/crear_cliente.html', {
        'form': form,
    })

def eliminar_cliente(request, pk):
    """
    Elimina un cliente.
    """
    cliente = get_object_or_404(Cliente, pk=pk, usuario=request.user)
    
    # Verificar que no esté en uso
    optimizaciones_usando = Optimizacion.objects.filter(cliente=cliente, usuario=request.user).count()
    proyectos_usando = Proyecto.objects.filter(cliente=cliente, usuario=request.user).count()
    
    if optimizaciones_usando > 0 or proyectos_usando > 0:
        messages.warning(
            request, 
            f'⚠️ No se puede eliminar el cliente "{cliente.nombre}" porque está siendo usado en {optimizaciones_usando} optimización(es) y {proyectos_usando} proyecto(s).'
        )
        return redirect('cutless:lista_clientes')
        
    if request.method == "POST":
        nombre = cliente.nombre
        cliente.delete()
        messages.success(request, f'✅ Cliente "{nombre}" eliminado exitosamente.')
        return redirect('cutless:lista_clientes')
    
    return render(request, 'cutless/eliminar_cliente.html', {
        'cliente': cliente,
    })

