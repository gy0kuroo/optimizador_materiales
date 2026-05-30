from decimal import Decimal

from django.contrib import messages
from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import render, redirect, get_object_or_404

from ..exports.pdf import generar_pdf_presupuesto as construir_pdf_presupuesto
from ..forms import PresupuestoForm
from ..models import Presupuesto, Optimizacion, Cliente
from ..services import enviar_notificacion


def lista_presupuestos(request):
    """
    Lista todos los presupuestos del usuario.
    """
    # Filtrar presupuestos del usuario
    presupuestos = Presupuesto.objects.filter(
        usuario=request.user
    ).prefetch_related('optimizaciones').select_related('cliente', 'proyecto').order_by('-fecha_creacion')
    
    # Filtros
    estado_filtro = request.GET.get('estado', '')
    if estado_filtro:
        presupuestos = presupuestos.filter(estado=estado_filtro)
    
    # Búsqueda
    busqueda = request.GET.get('busqueda', '').strip()
    if busqueda:
        presupuestos = presupuestos.filter(
            Q(numero__icontains=busqueda) |
            Q(cliente__nombre__icontains=busqueda)
        )
    
    return render(request, 'cutless/lista_presupuestos.html', {
        'presupuestos': presupuestos,
        'estado_filtro': estado_filtro,
        'busqueda': busqueda,
    })

def crear_presupuesto(request):
    """
    Crea un nuevo presupuesto desde una optimización.
    """
    # Si viene desde una optimización específica
    optimizacion_id = request.GET.get('optimizacion')
    optimizacion = None
    if optimizacion_id:
        optimizacion = get_object_or_404(Optimizacion, pk=optimizacion_id, usuario=request.user)
    
    if request.method == "POST":
        form = PresupuestoForm(request.POST, user=request.user)
        if form.is_valid():
            presupuesto = form.save(commit=False)
            presupuesto.usuario = request.user
            
            # Manejar nombre de cliente nuevo
            nombre_cliente_nuevo = form.cleaned_data.get('nombre_cliente_nuevo', '').strip()
            if nombre_cliente_nuevo:
                # Buscar o crear cliente con ese nombre
                cliente, created = Cliente.objects.get_or_create(
                    nombre=nombre_cliente_nuevo,
                    usuario=request.user,
                    defaults={'nombre': nombre_cliente_nuevo}
                )
                presupuesto.cliente = cliente
                if created:
                    messages.info(request, f'✅ Cliente "{nombre_cliente_nuevo}" creado automáticamente.')
            elif not presupuesto.cliente:
                # Si no hay cliente seleccionado ni nombre nuevo, usar el de la optimización si existe
                if optimizacion and optimizacion.cliente:
                    presupuesto.cliente = optimizacion.cliente
            
            # Generar número único
            presupuesto.numero = Presupuesto.generar_numero_presupuesto(usuario=request.user)
            
            # Calcular costo_total inicial antes del primer guardado
            # Usar las optimizaciones del formulario para calcular
            optimizaciones_seleccionadas = form.cleaned_data['optimizaciones']
            costo_total_inicial = Decimal('0.00')
            for optimizacion in optimizaciones_seleccionadas:
                num_tableros = optimizacion.num_tableros or 0
                costo_material = presupuesto.precio_tablero * Decimal(str(num_tableros))
                costo_total_inicial += costo_material
            costo_total_inicial += presupuesto.mano_obra
            presupuesto.costo_total = costo_total_inicial
            
            # Guardar primero para poder asignar las optimizaciones ManyToMany
            presupuesto.save()
            
            # Asignar optimizaciones (ManyToMany)
            presupuesto.optimizaciones.set(optimizaciones_seleccionadas)
            
            # Recalcular costo total (por si acaso) y guardar de nuevo
            presupuesto.costo_total = presupuesto.calcular_costo_total_multiple()
            presupuesto.save()
            
            num_optimizaciones = presupuesto.optimizaciones.count()
            
            # Enviar notificación de presupuesto creado (esto mostrará el mensaje según la configuración)
            enviar_notificacion(
                request,
                'presupuesto_creado',
                'Presupuesto Creado',
                f'Se ha creado el presupuesto #{presupuesto.numero} con un costo total de ${presupuesto.costo_total:.2f}.',
                {'presupuesto_id': presupuesto.id, 'numero': presupuesto.numero, 'costo_total': presupuesto.costo_total}
            )
            return redirect('cutless:detalle_presupuesto', pk=presupuesto.pk)
    else:
        form = PresupuestoForm(user=request.user)
        if optimizacion:
            # Prellenar datos desde la optimización
            form.fields['optimizaciones'].initial = [optimizacion]
            if optimizacion.cliente:
                form.fields['cliente'].initial = optimizacion.cliente
            if optimizacion.precio_tablero:
                form.fields['precio_tablero'].initial = optimizacion.precio_tablero
            if optimizacion.mano_obra:
                form.fields['mano_obra'].initial = optimizacion.mano_obra
            if optimizacion.proyecto:
                form.fields['proyecto'].initial = optimizacion.proyecto
    
    # Preparar información adicional de optimizaciones para el template
    optimizaciones_info = []
    optimizaciones_seleccionadas_ids = []
    if optimizacion:
        optimizaciones_seleccionadas_ids = [optimizacion.pk]
    
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
    
    return render(request, 'cutless/crear_presupuesto.html', {
        'form': form,
        'optimizacion': optimizacion,
        'optimizaciones_info': optimizaciones_info,
    })

def generar_pdf_presupuesto(request, pk):
    """
    Genera el PDF del presupuesto.
    """
    try:
        presupuesto = Presupuesto.objects.prefetch_related('optimizaciones').select_related('cliente').get(
            pk=pk,
            usuario=request.user
        )
    except Presupuesto.DoesNotExist:
        messages.error(request, "Presupuesto no encontrado.")
        return redirect('cutless:lista_presupuestos')
    
    # Generar PDF usando la función de utils
    pdf_path = construir_pdf_presupuesto(presupuesto)
    
    if pdf_path:
        presupuesto.pdf = pdf_path
        presupuesto.save()
        return FileResponse(open(pdf_path, 'rb'), content_type='application/pdf', filename=f'presupuesto_{presupuesto.numero}.pdf')
    else:
        messages.error(request, "Error al generar el PDF del presupuesto.")
        return redirect('cutless:detalle_presupuesto', pk=presupuesto.pk)

def detalle_presupuesto(request, pk):
    """
    Muestra el detalle de un presupuesto y permite generar PDF.
    """
    try:
        presupuesto = Presupuesto.objects.prefetch_related('optimizaciones').select_related('cliente', 'proyecto').get(
            pk=pk,
            usuario=request.user
        )
    except Presupuesto.DoesNotExist:
        messages.error(request, "Presupuesto no encontrado.")
        return redirect('cutless:lista_presupuestos')
    
    # Calcular información adicional para el template
    # Obtener todas las optimizaciones del usuario ordenadas por fecha descendente (igual que en historial)
    todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user).order_by('-fecha')
    total_optimizaciones = todas_optimizaciones.count()
    
    optimizaciones_con_costos = []
    for opt in presupuesto.optimizaciones.all():
        num_tableros = opt.num_tableros or 0
        costo_tableros = presupuesto.precio_tablero * Decimal(str(num_tableros))
        
        # Calcular el número de lista (basado en orden por fecha descendente)
        numero_lista = opt.pk  # Por defecto usar el ID
        for idx, optimizacion in enumerate(todas_optimizaciones, start=1):
            if optimizacion.id == opt.id:
                # Para orden descendente: numero = total - idx + 1
                numero_lista = total_optimizaciones - idx + 1
                break
        
        optimizaciones_con_costos.append({
            'optimizacion': opt,
            'num_tableros': num_tableros,
            'costo_tableros': costo_tableros,
            'numero_lista': numero_lista,
        })
    
    return render(request, 'cutless/detalle_presupuesto.html', {
        'presupuesto': presupuesto,
        'optimizaciones_con_costos': optimizaciones_con_costos,
        'total_tableros': presupuesto.get_total_tableros(),
    })

def editar_presupuesto(request, pk):
    """
    Edita un presupuesto existente.
    """
    try:
        presupuesto = Presupuesto.objects.prefetch_related('optimizaciones').select_related('cliente', 'proyecto').get(
            pk=pk,
            usuario=request.user
        )
    except Presupuesto.DoesNotExist:
        messages.error(request, "Presupuesto no encontrado.")
        return redirect('cutless:lista_presupuestos')
    
    if request.method == "POST":
        form = PresupuestoForm(request.POST, instance=presupuesto, user=request.user)
        if form.is_valid():
            presupuesto = form.save(commit=False)
            
            # Manejar nombre de cliente nuevo
            nombre_cliente_nuevo = form.cleaned_data.get('nombre_cliente_nuevo', '').strip()
            if nombre_cliente_nuevo:
                # Buscar o crear cliente con ese nombre
                cliente, created = Cliente.objects.get_or_create(
                    nombre=nombre_cliente_nuevo,
                    usuario=request.user,
                    defaults={'nombre': nombre_cliente_nuevo}
                )
                presupuesto.cliente = cliente
                if created:
                    messages.info(request, f'✅ Cliente "{nombre_cliente_nuevo}" creado automáticamente.')
            
            # Guardar primero para poder asignar las optimizaciones ManyToMany
            presupuesto.save()
            
            # Asignar optimizaciones (ManyToMany)
            optimizaciones_seleccionadas = form.cleaned_data['optimizaciones']
            presupuesto.optimizaciones.set(optimizaciones_seleccionadas)
            
            # Recalcular costo total y guardar de nuevo
            presupuesto.costo_total = presupuesto.calcular_costo_total_multiple()
            presupuesto.save()
            
            num_optimizaciones = presupuesto.optimizaciones.count()
            messages.success(request, f'✅ Presupuesto "{presupuesto.numero}" actualizado exitosamente con {num_optimizaciones} optimización(es).')
            return redirect('cutless:detalle_presupuesto', pk=presupuesto.pk)
    else:
        form = PresupuestoForm(instance=presupuesto, user=request.user)
    
    # Preparar información adicional de optimizaciones para el template
    optimizaciones_info = []
    optimizaciones_seleccionadas_ids = list(presupuesto.optimizaciones.values_list('pk', flat=True))
    
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
    
    return render(request, 'cutless/editar_presupuesto.html', {
        'form': form,
        'presupuesto': presupuesto,
        'optimizaciones_info': optimizaciones_info,
    })

def agregar_optimizaciones_presupuesto(request, pk):
    """
    Permite agregar múltiples optimizaciones a un presupuesto existente.
    """
    try:
        presupuesto = Presupuesto.objects.prefetch_related('optimizaciones').get(
            pk=pk,
            usuario=request.user
        )
    except Presupuesto.DoesNotExist:
        messages.error(request, "Presupuesto no encontrado.")
        return redirect('cutless:lista_presupuestos')
    
    # Obtener optimizaciones que aún no están en el presupuesto
    optimizaciones_en_presupuesto = presupuesto.optimizaciones.values_list('pk', flat=True)
    optimizaciones_disponibles = Optimizacion.objects.filter(
        usuario=request.user
    ).exclude(pk__in=optimizaciones_en_presupuesto).order_by('-fecha')
    
    if request.method == "POST":
        optimizaciones_ids = request.POST.getlist('optimizaciones')
        if optimizaciones_ids:
            optimizaciones_seleccionadas = Optimizacion.objects.filter(
                pk__in=optimizaciones_ids,
                usuario=request.user
            )
            # Agregar las optimizaciones al presupuesto (ManyToMany)
            presupuesto.optimizaciones.add(*optimizaciones_seleccionadas)
            
            # Recalcular costo total
            presupuesto.costo_total = presupuesto.calcular_costo_total_multiple()
            presupuesto.save()
            
            messages.success(
                request, 
                f'✅ {optimizaciones_seleccionadas.count()} optimización(es) agregada(s) al presupuesto "{presupuesto.numero}".'
            )
            return redirect('cutless:detalle_presupuesto', pk=presupuesto.pk)
        else:
            messages.warning(request, "Debes seleccionar al menos una optimización.")
    
    return render(request, 'cutless/agregar_optimizaciones_presupuesto.html', {
        'presupuesto': presupuesto,
        'optimizaciones_disponibles': optimizaciones_disponibles,
    })

