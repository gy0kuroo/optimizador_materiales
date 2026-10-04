"""Acceso autenticado a archivos generados, según su propietario en la BD."""
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import FileResponse, Http404
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe

from ..models import Optimizacion, Presupuesto, TableroOptimizacion


@login_required
@require_safe
@never_cache
def media_privada(request, archivo):
    if '\\' in archivo or ':' in archivo:
        raise Http404
    raiz = Path(settings.MEDIA_ROOT).resolve()
    ruta = (raiz / archivo).resolve()
    try:
        relativo = ruta.relative_to(raiz).as_posix()
    except ValueError:
        raise Http404
    tipos = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.pdf': 'application/pdf'}
    if ruta.suffix.lower() not in tipos:
        raise Http404
    nombres = [relativo, str(ruta)]  # Compatibilidad con referencias absolutas antiguas.
    propietario = (
        Optimizacion.objects.filter(usuario=request.user).filter(Q(imagen__in=nombres) | Q(pdf__in=nombres)).exists()
        or TableroOptimizacion.objects.filter(optimizacion__usuario=request.user, imagen__in=nombres).exists()
        or Presupuesto.objects.filter(usuario=request.user, pdf__in=nombres).exists()
    )
    if not propietario:
        raise Http404
    # Una ruta heredada compartida entre propietarios no identifica un archivo privado.
    compartido = (
        Optimizacion.objects.exclude(usuario=request.user).filter(Q(imagen__in=nombres) | Q(pdf__in=nombres)).exists()
        or TableroOptimizacion.objects.exclude(optimizacion__usuario=request.user).filter(imagen__in=nombres).exists()
        or Presupuesto.objects.exclude(usuario=request.user).filter(pdf__in=nombres).exists()
    )
    if compartido:
        raise Http404
    try:
        respuesta = FileResponse(ruta.open('rb'), content_type=tipos[ruta.suffix.lower()])
    except (FileNotFoundError, IsADirectoryError):
        raise Http404
    respuesta['X-Content-Type-Options'] = 'nosniff'
    return respuesta
