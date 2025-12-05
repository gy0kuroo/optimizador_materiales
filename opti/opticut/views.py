from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory
from django.core.files.base import ContentFile
from .forms import TableroForm, PiezaForm
from .models import Optimizacion
from .utils import generar_grafico, generar_pdf
import base64
from django.contrib import messages
from django.http import FileResponse
import os
from opti import settings

@login_required
def index(request):
    # Limpiar mensajes antiguos al cargar el formulario por primera vez
    if request.method == "GET":
        storage = messages.get_messages(request)
        storage.used = True
    
    PiezaFormSet = formset_factory(PiezaForm, extra=3, max_num=20, validate_max=True)

    if request.method == "POST":
        tablero_form = TableroForm(request.POST)
        pieza_formset = PiezaFormSet(request.POST)

        if tablero_form.is_valid() and pieza_formset.is_valid():
            ancho = tablero_form.cleaned_data["ancho"]
            alto = tablero_form.cleaned_data["alto"]

            piezas = []
            piezas_con_nombre = []
            
            for form in pieza_formset:
                # Verificar si el formulario tiene datos COMPLETOS
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    # Obtener los valores
                    pieza_ancho = form.cleaned_data.get("ancho")
                    pieza_alto = form.cleaned_data.get("alto")
                    cantidad = form.cleaned_data.get("cantidad")
                    nombre = form.cleaned_data.get("nombre", "").strip()
                    
                    # IMPORTANTE: Solo procesar si tiene ancho Y alto
                    if pieza_ancho and pieza_alto and cantidad:
                        # Si no hay nombre, asignar uno por defecto
                        if not nombre:
                            nombre = f"Pieza {len(piezas_con_nombre) + 1}"
                        
                        # Validar que la pieza no sea más grande que el tablero
                        if pieza_ancho > ancho or pieza_alto > alto:
                            messages.error(
                                request, 
                                f"❌ La pieza '{nombre}' ({pieza_ancho}x{pieza_alto} cm) NO CABE en el tablero ({ancho}x{alto} cm)."
                            )
                            return render(request, "opticut/index.html", {
                                "tablero_form": tablero_form,
                                "pieza_formset": pieza_formset
                            })
                        
                        piezas.append((pieza_ancho, pieza_alto, cantidad))
                        piezas_con_nombre.append({
                            'nombre': nombre,
                            'ancho': pieza_ancho,
                            'alto': pieza_alto,
                            'cantidad': cantidad
                        })
            
            # Validar que haya al menos una pieza
            if not piezas:
                messages.error(request, "❌ Debes agregar al menos una pieza con dimensiones válidas.")
                return render(request, "opticut/index.html", {
                    "tablero_form": tablero_form,
                    "pieza_formset": pieza_formset
                })

            # Generar TODAS las imágenes, aprovechamiento Y desperdicio
            imagenes_base64, aprovechamiento, info_desperdicio = generar_grafico(piezas, ancho, alto)
            
            # Usar la primera imagen para vista previa
            imagen_principal = imagenes_base64[0] if imagenes_base64 else ""

            # Guardar en BD (ahora con nombres)
            piezas_texto = "\n".join([
                f"{p['nombre']},{p['ancho']},{p['alto']},{p['cantidad']}" 
                for p in piezas_con_nombre
            ])
            
            optimizacion = Optimizacion.objects.create(
                usuario=request.user,
                ancho_tablero=ancho,
                alto_tablero=alto,
                piezas=piezas_texto,
                aprovechamiento_total=aprovechamiento
            )

            # Guardar la primera imagen en el FileField
            if imagen_principal:
                image_data = base64.b64decode(imagen_principal)
                file = ContentFile(image_data, name=f"optimizacion_{request.user.username}_{optimizacion.id}.png")
                optimizacion.imagen.save(f"optimizacion_{request.user.username}_{optimizacion.id}.png", file)
            
            # Generar UN SOLO PDF con todos los tableros
            try:
                pdf_path = generar_pdf(optimizacion, imagenes_base64)
            except Exception as e:
                messages.warning(request, f"⚠️ PDF no generado: {str(e)}")
                pdf_path = None
            
            messages.success(request, f"✅ Optimización creada exitosamente. Aprovechamiento: {aprovechamiento:.2f}%")
            
            return render(request, "opticut/resultado.html", {
                "imagen": imagen_principal,
                "imagenes": imagenes_base64,
                "optimizacion": optimizacion,
                "pdf_path": pdf_path,
                "num_tableros": len(imagenes_base64),
                "piezas_con_nombre": piezas_con_nombre,
                "info_desperdicio": info_desperdicio  # AGREGADO
            })
        else:
            # Mostrar errores de validación
            if not tablero_form.is_valid():
                messages.error(request, "❌ Error en las dimensiones del tablero.")
            if not pieza_formset.is_valid():
                messages.error(request, "❌ Error en los datos de las piezas.")

    else:
        tablero_form = TableroForm()
        pieza_formset = PiezaFormSet()

    return render(request, "opticut/index.html", {
        "tablero_form": tablero_form,
        "pieza_formset": pieza_formset
    })


@login_required
def mis_optimizaciones(request):
    optimizaciones = Optimizacion.objects.filter(usuario=request.user)
    
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
    
    # Ordenar por fecha descendente (más recientes primero)
    optimizaciones = optimizaciones.order_by('-fecha')
    total_optimizaciones = optimizaciones.count()
    
    # Procesar piezas para cada optimización
    optimizaciones_con_piezas = []
    for idx, opt in enumerate(optimizaciones, start=1):
        numero_mostrado = total_optimizaciones - idx + 1
        piezas_procesadas = []
        for linea in opt.piezas.splitlines():
            if linea.strip():
                partes = linea.split(',')
                if len(partes) == 4:  # Formato: nombre,ancho,alto,cantidad
                    piezas_procesadas.append({
                        'nombre': partes[0].strip(),
                        'ancho': partes[1].strip(),
                        'alto': partes[2].strip(),
                        'cantidad': partes[3].strip()
                    })
                elif len(partes) == 3:  # Formato antiguo: ancho,alto,cantidad
                    piezas_procesadas.append({
                        'nombre': 'Pieza',
                        'ancho': partes[0].strip(),
                        'alto': partes[1].strip(),
                        'cantidad': partes[2].strip()
                    })
        
        optimizaciones_con_piezas.append({
            'optimizacion': opt,
            'piezas': piezas_procesadas,
            'numero': numero_mostrado
        })
    
    return render(request, 'opticut/mis_optimizaciones.html', {
        'optimizaciones_con_piezas': optimizaciones_con_piezas,
        'nombre_pieza': nombre_pieza,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    })




@login_required
def borrar_historial(request):
    if request.method == "POST":
        optimizaciones = Optimizacion.objects.filter(usuario=request.user)
        count = optimizaciones.count()
        optimizaciones.delete()
        messages.success(request, f"Se eliminaron {count} optimizaciones del historial.")
        return redirect('opticut:mis_optimizaciones')
    else:
        messages.error(request, "Operación no permitida.")
        return redirect('opticut:mis_optimizaciones')


@login_required
def borrar_optimizacion(request, pk):
    """
    Elimina una optimización individual del usuario actual.
    """
    try:
        optimizacion = Optimizacion.objects.get(pk=pk, usuario=request.user)
        optimizacion.delete()
        messages.success(request, f"Optimización #{pk} eliminada correctamente.")
    except Optimizacion.DoesNotExist:
        messages.error(request, "No se encontró la optimización o no tienes permiso para eliminarla.")

    return redirect('opticut:mis_optimizaciones')


@login_required
def descargar_pdf(request, pk):
    try:
        optimizacion = Optimizacion.objects.get(pk=pk, usuario=request.user)
        
        # Calcular el número de lista (mismo método que en mis_optimizaciones)
        todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user).order_by('-fecha')
        total_optimizaciones = todas_optimizaciones.count()
        
        # Encontrar la posición de esta optimización en la lista
        for idx, opt in enumerate(todas_optimizaciones, start=1):
            if opt.id == optimizacion.id:
                numero_lista = total_optimizaciones - idx + 1
                break
        else:
            numero_lista = None  # Si no se encuentra, usar ID por defecto
        
        # Regenerar las imágenes desde los datos guardados
        piezas = []
        for linea in optimizacion.piezas.splitlines():
            partes = linea.split(",")
            if len(partes) == 4:  # Con nombre
                nombre, w, h, c = partes
                piezas.append((int(w), int(h), int(c)))
            else:  # Sin nombre (formato antiguo)
                w, h, c = partes
                piezas.append((int(w), int(h), int(c)))
        
        # Generar TODAS las imágenes nuevamente (con info de desperdicio)
        imagenes_base64, _, info_desperdicio = generar_grafico(piezas, optimizacion.ancho_tablero, optimizacion.alto_tablero)
        
        # Generar UN SOLO PDF con todas las imágenes (usando número de lista)
        pdf_path = generar_pdf(optimizacion, imagenes_base64, numero_lista=numero_lista)
        
        full_path = os.path.join(settings.MEDIA_ROOT, pdf_path)
        return FileResponse(open(full_path, "rb"), as_attachment=True, filename=os.path.basename(full_path))
    except Exception as e:
        messages.error(request, f"Error generando PDF: {e}")
        return redirect('opticut:mis_optimizaciones')


@login_required
def resultado_view(request):
    if request.method == "POST":
        ancho = int(request.POST.get("ancho_tablero"))
        alto = int(request.POST.get("alto_tablero"))
        piezas_texto = request.POST.get("piezas")

        piezas = []
        for linea in piezas_texto.strip().splitlines():
            partes = linea.split(",")
            if len(partes) == 4:  # Con nombre
                nombre, w, h, c = partes
                piezas.append((int(w), int(h), int(c)))
            else:  # Sin nombre
                w, h, c = partes
                piezas.append((int(w), int(h), int(c)))

        # Generar TODAS las imágenes con info de desperdicio
        imagenes_base64, aprovechamiento, info_desperdicio = generar_grafico(piezas, ancho, alto)
        imagen_principal = imagenes_base64[0] if imagenes_base64 else ""

        optimizacion = Optimizacion.objects.create(
            usuario=request.user,
            ancho_tablero=ancho,
            alto_tablero=alto,
            piezas=piezas_texto,
            aprovechamiento_total=aprovechamiento
        )

        # Guardar la primera imagen en el modelo
        if imagen_principal:
            image_data = base64.b64decode(imagen_principal)
            file = ContentFile(image_data)
            optimizacion.imagen.save(f"optimizacion_{request.user.username}_{optimizacion.id}.png", file)

        # Generar UN SOLO PDF con todas las imágenes
        pdf_path = generar_pdf(optimizacion, imagenes_base64)
        optimizacion.pdf = pdf_path
        optimizacion.save()

        return render(request, "opticut/resultado.html", {
            "optimizacion": optimizacion,
            "imagen": imagen_principal,
            "imagenes": imagenes_base64,
            "pdf_path": pdf_path,
            "num_tableros": len(imagenes_base64),
            "info_desperdicio": info_desperdicio
        })


@login_required
def duplicar_optimizacion(request, pk):
    """
    Duplica una optimización existente y carga sus datos en el formulario.
    """
    try:
        optimizacion = Optimizacion.objects.get(pk=pk, usuario=request.user)
        
        # Parsear las piezas guardadas
        piezas_data = []
        for linea in optimizacion.piezas.splitlines():
            partes = linea.split(',')
            if len(partes) == 4:  # Con nombre
                nombre, ancho, alto, cantidad = partes
                piezas_data.append({
                    'nombre': nombre.strip(),
                    'ancho': int(ancho.strip()),
                    'alto': int(alto.strip()),
                    'cantidad': int(cantidad.strip())
                })
            else:  # Sin nombre (formato antiguo)
                ancho, alto, cantidad = partes
                piezas_data.append({
                    'nombre': '',
                    'ancho': int(ancho.strip()),
                    'alto': int(alto.strip()),
                    'cantidad': int(cantidad.strip())
                })
        
        # Crear formset con los datos de la optimización
        PiezaFormSet = formset_factory(PiezaForm, extra=0, max_num=20)
        
        # Crear formularios con datos prellenados
        tablero_form = TableroForm(initial={
            'ancho': optimizacion.ancho_tablero,
            'alto': optimizacion.alto_tablero
        })
        
        pieza_formset = PiezaFormSet(initial=piezas_data)
        
        messages.info(request, f"📋 Cargando datos de la optimización #{pk}. Puedes modificarlos antes de calcular.")
        
        return render(request, "opticut/index.html", {
            "tablero_form": tablero_form,
            "pieza_formset": pieza_formset,
            "duplicando": True,
            "optimizacion_original": optimizacion
        })
        
    except Optimizacion.DoesNotExist:
        messages.error(request, "No se encontró la optimización.")
        return redirect('opticut:mis_optimizaciones')