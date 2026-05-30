from functools import wraps

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, redirect

from ..models import Material


def handler404(request, exception):
    """Maneja errores 404 con una página personalizada"""
    return render(request, 'cutless/404.html', status=404)


def requiere_permiso(permiso_nombre):
    """Decorador para verificar si el usuario tiene un permiso específico en su perfil."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('usuarios:login')

            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            try:
                perfil = request.user.perfil
            except AttributeError:
                return redirect('usuarios:login')

            if getattr(perfil, 'rol', None) == 'admin':
                return view_func(request, *args, **kwargs)

            if not getattr(perfil, permiso_nombre, False):
                messages.error(request, "❌ No tienes permiso para acceder a esta funcionalidad.")
                return redirect('cutless:index')

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def handler500(request):
    """Maneja errores 500 con una página personalizada"""
    return render(request, 'cutless/500.html', status=500)


def _materiales_data_json_index(user):
    """JSON de materiales para la plantilla index (errores / reintentos)."""
    import json
    materiales_data = {}
    filtro = Q(es_predefinido=True)
    if getattr(user, 'is_authenticated', False):
        filtro = Q(usuario=user) | Q(es_predefinido=True)
    for material in Material.objects.filter(filtro):
        materiales_data[str(material.pk)] = {
            'precio': float(material.precio) if material.precio else None,
            'nombre': material.nombre,
            'ancho': float(material.ancho) if material.ancho else None,
            'alto': float(material.alto) if material.alto else None,
            'unidad_medida': material.unidad_medida if material.unidad_medida else 'cm',
        }
    return json.dumps(materiales_data)
