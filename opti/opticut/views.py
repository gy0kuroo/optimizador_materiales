from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory
from django.core.files.base import ContentFile
from .forms import TableroForm, PiezaForm
from .models import Optimizacion
from .utils import generar_grafico
import base64

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

            # Generar la imagen y el aprovechamiento
            imagen_base64, aprovechamiento = generar_grafico(piezas, ancho, alto)

            # Guardar imagen como archivo
            image_data = base64.b64decode(imagen_base64)
            file = ContentFile(image_data, name=f"optimizacion_{request.user.username}.png")

            # Guardar en BD (primero los datos, luego la imagen)
            piezas_texto = "\n".join([f"{w},{h},{c}" for w, h, c in piezas])
            optimizacion = Optimizacion.objects.create(
                usuario=request.user,
                ancho_tablero=ancho,
                alto_tablero=alto,
                piezas=piezas_texto,
                aprovechamiento_total=aprovechamiento
            )

            # Guardar archivo físico en el FileField
            optimizacion.imagen.save(f"optimizacion_{request.user.username}.png", file)

            return render(request, "opticut/resultado.html", {
                "imagen": imagen_base64,
                "optimizacion": optimizacion,
            })

    else:
        tablero_form = TableroForm()
        pieza_formset = PiezaFormSet()

    return render(request, "opticut/index.html", {
        "tablero_form": tablero_form,
        "pieza_formset": pieza_formset
    })
