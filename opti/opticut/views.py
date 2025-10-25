from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory
from django.core.files.base import ContentFile
from .forms import TableroForm, PiezaForm
from .models import Optimizacion
from .utils import generar_grafico, generar_pdf
import base64
from django.shortcuts import render
from .models import Optimizacion
from django.contrib import messages
from django.http import FileResponse
import os
from opti import settings

@login_required
def index(request):
    PiezaFormSet = formset_factory(PiezaForm, extra=3)

    if request.method == "POST":
        tablero_form = TableroForm(request.POST)
        pieza_formset = PiezaFormSet(request.POST)

        if tablero_form.is_valid() and pieza_formset.is_valid():
            ancho = tablero_form.cleaned_data["ancho"]
            alto = tablero_form.cleaned_data["alto"]

            piezas = []
            for form in pieza_formset:
                if form.cleaned_data:
                    piezas.append((
                        form.cleaned_data["ancho"],
                        form.cleaned_data["alto"],
                        form.cleaned_data["cantidad"]
                    ))

            # Generar TODAS las imágenes y el aprovechamiento
            imagenes_base64, aprovechamiento = generar_grafico(piezas, ancho, alto)
            
            # Usar la primera imagen para vista previa
            imagen_principal = imagenes_base64[0] if imagenes_base64 else ""

            # Guardar en BD
            piezas_texto = "\n".join([f"{w},{h},{c}" for w, h, c in piezas])
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
            pdf_path = generar_pdf(optimizacion, imagenes_base64)
            
            return render(request, "opticut/resultado.html", {
                "imagen": imagen_principal,
                "imagenes": imagenes_base64,  # Lista con todas las imágenes
                "optimizacion": optimizacion,
                "pdf_path": pdf_path,  # Una sola ruta de PDF
                "num_tableros": len(imagenes_base64)
            })

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
            w, h, c = map(int, linea.split(","))
            piezas.append((w, h, c))
        
        # Generar TODAS las imágenes nuevamente
        imagenes_base64, _ = generar_grafico(piezas, optimizacion.ancho_tablero, optimizacion.alto_tablero)
        
        # Generar UN SOLO PDF con todas las imágenes
        pdf_path = generar_pdf(optimizacion, imagenes_base64)
        
        full_path = os.path.join(settings.MEDIA_ROOT, pdf_path)
        return FileResponse(open(full_path, "rb"), as_attachment=True, filename=os.path.basename(full_path))
    except Exception as e:
        messages.error(request, f"Error generando PDF: {e}")
        return redirect('opticut:mis_optimizaciones')

def resultado_view(request):
    if request.method == "POST":
        ancho = int(request.POST.get("ancho_tablero"))
        alto = int(request.POST.get("alto_tablero"))
        piezas_texto = request.POST.get("piezas")

        piezas = []
        for linea in piezas_texto.strip().splitlines():
            w, h, c = map(int, linea.split(","))
            piezas.append((w, h, c))

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
            "pdf_path": pdf_path,  # Una sola ruta
            "num_tableros": len(imagenes_base64)
        })cl