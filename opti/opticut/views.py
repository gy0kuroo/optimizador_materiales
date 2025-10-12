from django.shortcuts import render
from .forms import TableroForm
from .utils import generar_grafico
from django.http import HttpResponse


def index(request):
    if request.method == "POST":
        form = TableroForm(request.POST)
        if form.is_valid():
            ancho = form.cleaned_data["ancho"]
            alto = form.cleaned_data["alto"]
            piezas_raw = form.cleaned_data["piezas"].strip().split("\n")
            piezas = []
            for linea in piezas_raw:
                w, h, cant = map(int, linea.split(","))
                piezas.append((w, h, cant))

            imagen_base64 = generar_grafico(piezas, ancho, alto)
            return render(request, "opticut/resultado.html", {"imagen": imagen_base64})
    else:
        form = TableroForm()
    return render(request, "opticut/index.html", {"form": form})
