from django.shortcuts import render
from django.forms import formset_factory
from .forms import TableroForm, PiezaForm
from .utils import generar_grafico
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    PiezaFormSet = formset_factory(PiezaForm, extra=3)  # permite 3 piezas por defecto

    if request.method == "POST":
        tablero_form = TableroForm(request.POST)
        pieza_formset = PiezaFormSet(request.POST)

        if tablero_form.is_valid() and pieza_formset.is_valid():
            ancho = tablero_form.cleaned_data["ancho"]
            alto = tablero_form.cleaned_data["alto"]

            piezas = []
            for form in pieza_formset:
                if form.cleaned_data:  # evita errores por filas vacías
                    piezas.append((
                        form.cleaned_data["ancho"],
                        form.cleaned_data["alto"],
                        form.cleaned_data["cantidad"]
                    ))

            imagen_base64 = generar_grafico(piezas, ancho, alto)
            return render(request, "opticut/resultado.html", {"imagen": imagen_base64})

    else:
        tablero_form = TableroForm()
        pieza_formset = PiezaFormSet()

    return render(request,'opticut/index.html', {
        "tablero_form": tablero_form,
        "pieza_formset": pieza_formset
    })