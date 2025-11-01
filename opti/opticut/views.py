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
    PiezaFormSet = formset_factory(PiezaForm, extra=3, max_num=20, validate_max=True)
    # Limpiar mensajes antiguos al cargar el formulario por primera vez
    if request.method == "GET":
            print("=" * 50)
    print("POST DATA:", request.POST)
    print("=" * 50)
    
    tablero_form = TableroForm(request.POST)
    pieza_formset = PiezaFormSet(request.POST)
    
    print("Tablero form válido:", tablero_form.is_valid())
    print("Pieza formset válido:", pieza_formset.is_valid())
    
    if pieza_formset.is_valid():
        print("Número de formularios:", len(pieza_formset))
        for i, form in enumerate(pieza_formset):
            print(f"Form {i}: {form.cleaned_data}")
    else:
        print("Errores del formset:", pieza_formset.errors)
        storage = messages.get_messages(request)
        storage.used = True
    
    
    
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
                    
                    # IMPORTANTE: Solo procesar si tiene ancho Y alto (no solo cleaned_data)
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

            # Generar TODAS las imágenes y el aprovechamiento
            imagenes_base64, aprovechamiento = generar_grafico(piezas, ancho, alto)
            
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
                "piezas_con_nombre": piezas_con_nombre
            })
        else:
            # Mostrar errores de validación
            if not tablero_form.is_valid():
                messages.error(request, "❌ Error en las dimensiones del tablero.")
            if not pieza_formset.is_valid():
                messages.error(request, "❌ Error en los datos de las piezas.")
                # Mostrar errores específicos del formset
                for i, form in enumerate(pieza_formset):
                    if form.errors:
                        messages.error(request, f"Pieza #{i+1}: {form.errors}")

    else:
        tablero_form = TableroForm()
        pieza_formset = PiezaFormSet()

    return render(request, "opticut/index.html", {
        "tablero_form": tablero_form,
        "pieza_formset": pieza_formset
    })

@login_required
def mis_optimizaciones(request):
    optimizaciones = Optimizacion.objects.filter(usuario=request.user).order_by('-fecha')
    return render(request, 'opticut/mis_optimizaciones.html', {
        'optimizaciones': optimizaciones
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
        
        # Generar TODAS las imágenes nuevamente
        imagenes_base64, _ = generar_grafico(piezas, optimizacion.ancho_tablero, optimizacion.alto_tablero)
        
        # Generar UN SOLO PDF con todas las imágenes
        pdf_path = generar_pdf(optimizacion, imagenes_base64)
        
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

        # Generar TODAS las imágenes
        imagenes_base64, aprovechamiento = generar_grafico(piezas, ancho, alto)
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
            "num_tableros": len(imagenes_base64)
        })