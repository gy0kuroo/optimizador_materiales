# Imports estándar de Python
import base64
import os
from datetime import timedelta
from decimal import Decimal

# Imports de Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db.models import Avg, Count, Sum, Max, Min, Q
from django.forms import formset_factory
from django.http import FileResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.utils import timezone

# Imports del proyecto
from django.conf import settings
from ..forms import TableroForm, PiezaForm, MaterialForm, ClienteForm, PresupuestoForm, ProyectoForm, PlantillaForm
from ..models import Optimizacion, Material, Cliente, Presupuesto, Proyecto, Plantilla
from ..utils import (
    convertir_a_cm, convertir_desde_cm, generar_excel, generar_grafico,
    generar_grafico_aprovechamiento, generar_grafico_desperdicio, generar_pdf,
    generar_excel_resumen_desperdicio, generar_pdf_resumen_desperdicio,
    mensaje_advertencia_piezas_no_colocadas, obtener_simbolo_area, obtener_simbolo_unidad,
    parsear_piezas_desde_texto,
    pieza_cabe_en_tablero,
)
from ..utils_notificaciones import enviar_notificacion
from ..services import (
    calcular_numero_lista,
    persistir_resultado_optimizacion,
    obtener_resultado_optimizacion,
    preparar_contexto_resultado,
    pdf_path_para_template,
    respuesta_png_tablero,
    respuesta_pdf_optimizacion,
)
def handler404(request, exception):
    """Maneja errores 404 con una página personalizada"""
    return render(request, 'cutless/404.html', status=404)

def requiere_permiso(permiso_nombre):
    """Decorador para verificar si el usuario tiene un permiso específico"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('usuarios:login')
            
            try:
                perfil = request.user.perfil
                permiso_activo = getattr(perfil, permiso_nombre, False)
                
                if not permiso_activo:
                    messages.error(request, f"❌ No tienes permiso para acceder a esta funcionalidad.")
                    return redirect('cutless:index')
            except:
                return redirect('usuarios:login')
            
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
    for material in Material.objects.filter(
        Q(usuario=user) | Q(es_predefinido=True)
    ):
        materiales_data[str(material.pk)] = {
            'precio': float(material.precio) if material.precio else None,
            'nombre': material.nombre,
            'ancho': float(material.ancho) if material.ancho else None,
            'alto': float(material.alto) if material.alto else None,
            'unidad_medida': material.unidad_medida if material.unidad_medida else 'cm'
        }
    return json.dumps(materiales_data)

