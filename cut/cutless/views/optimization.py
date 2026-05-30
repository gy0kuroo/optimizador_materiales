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
    respuesta_png_tablero,
    respuesta_pdf_optimizacion,
)
from .common import _materiales_data_json_index, requiere_permiso
def editar_optimizacion(request, pk):
    """
    Permite editar una optimización existente.
    """
    optimizacion = get_object_or_404(Optimizacion, pk=pk, usuario=request.user)
    
    # Crear formset con solo 1 formulario extra vacío para edición
    PiezaFormSet = formset_factory(PiezaForm, extra=1, max_num=20, validate_max=True)
    
    if request.method == "POST":
        tablero_form = TableroForm(request.POST)
        pieza_formset = PiezaFormSet(request.POST)
        
        if tablero_form.is_valid() and pieza_formset.is_valid():
            # Obtener unidad seleccionada
            unidad = tablero_form.cleaned_data.get("unidad_medida", "cm")
            
            # Obtener valores en la unidad del usuario
            ancho_usuario = tablero_form.cleaned_data["ancho"]
            alto_usuario = tablero_form.cleaned_data["alto"]
            
            # Convertir a cm para cálculos internos
            ancho = convertir_a_cm(ancho_usuario, unidad)
            alto = convertir_a_cm(alto_usuario, unidad)

            permitir_rotacion = tablero_form.cleaned_data.get('permitir_rotacion', True)
            
            piezas = []
            piezas_con_nombre = []
            
            for form in pieza_formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    pieza_ancho = form.cleaned_data.get("ancho")
                    pieza_alto = form.cleaned_data.get("alto")
                    cantidad = form.cleaned_data.get("cantidad")
                    nombre = form.cleaned_data.get("nombre", "").strip()
                    
                    if pieza_ancho and pieza_alto and cantidad:
                        if not nombre:
                            nombre = f"Pieza {len(piezas_con_nombre) + 1}"
                        
                        pieza_ancho_cm = convertir_a_cm(pieza_ancho, unidad)
                        pieza_alto_cm = convertir_a_cm(pieza_alto, unidad)
                        
                        if not pieza_cabe_en_tablero(
                            pieza_ancho_cm, pieza_alto_cm, ancho, alto,
                            permitir_rotacion=permitir_rotacion,
                        ):
                            simbolo = obtener_simbolo_unidad(unidad)
                            sug = ''
                            if (not permitir_rotacion and pieza_cabe_en_tablero(
                                pieza_ancho_cm, pieza_alto_cm, ancho, alto,
                                permitir_rotacion=True,
                            )):
                                sug = (
                                    ' Prueba activar «Rotación automática»: con rotación sí cabe como una sola pieza.'
                                )
                            messages.error(
                                request,
                                f"❌ La pieza «{nombre}» ({pieza_ancho}×{pieza_alto} {simbolo}) NO CABE "
                                f"como placas rectangulares en el tablero ({ancho_usuario}×{alto_usuario} {simbolo})."
                                f"{sug}"
                            )
                            return render(request, "cutless/editar_optimizacion.html", {
                                "tablero_form": tablero_form,
                                "pieza_formset": pieza_formset,
                                "optimizacion": optimizacion
                            })
                        
                        piezas.append((pieza_ancho_cm, pieza_alto_cm, cantidad))
                        piezas_con_nombre.append({
                            'nombre': nombre,
                            'ancho': pieza_ancho,
                            'alto': pieza_alto,
                            'cantidad': cantidad
                        })
            
            if not piezas:
                messages.error(request, "❌ Debes agregar al menos una pieza con dimensiones válidas.")
                return render(request, "cutless/editar_optimizacion.html", {
                    "tablero_form": tablero_form,
                    "pieza_formset": pieza_formset,
                    "optimizacion": optimizacion
                })
            
            margen_corte_mm = tablero_form.cleaned_data.get('margen_corte') or 3  # Siempre en mm, default 3
            margen_corte_cm = margen_corte_mm / 10.0
            
            # Obtener datos de costos
            material_seleccionado = tablero_form.cleaned_data.get('material')
            precio_tablero = tablero_form.cleaned_data.get('precio_tablero')
            mano_obra = tablero_form.cleaned_data.get('mano_obra') or 0
            
            # Si se seleccionó un material y no hay precio manual, usar el del material
            if material_seleccionado and not precio_tablero:
                precio_tablero = material_seleccionado.precio
            
            # Obtener cliente y proyecto si se seleccionaron
            cliente_seleccionado = tablero_form.cleaned_data.get('cliente')
            proyecto_seleccionado = tablero_form.cleaned_data.get('proyecto')

            # Extraer nombres de piezas para colores consistentes
            nombres_piezas = [p['nombre'] for p in piezas_con_nombre]
            
            # Generar nuevas imágenes
            imagenes_base64, aprovechamiento, info_desperdicio = generar_grafico(
                piezas, ancho, alto, unidad, 
                permitir_rotacion=permitir_rotacion, 
                margen_corte=margen_corte_cm,
                nombres_piezas=nombres_piezas
            )

            ncol = info_desperdicio.get('num_piezas_colocadas') or 0
            nsol = info_desperdicio.get('num_piezas_solicitadas') or 0
            if nsol > 0 and ncol == 0:
                warn = mensaje_advertencia_piezas_no_colocadas(info_desperdicio, unidad)
                messages.error(request, warn or '❌ No se pudo colocar ninguna pieza en el tablero.')
                return render(request, "cutless/editar_optimizacion.html", {
                    "tablero_form": tablero_form,
                    "pieza_formset": pieza_formset,
                    "optimizacion": optimizacion,
                })

            warn_omitidas = mensaje_advertencia_piezas_no_colocadas(info_desperdicio, unidad)
            if warn_omitidas:
                messages.warning(request, warn_omitidas)
            
            imagen_principal = imagenes_base64[0] if imagenes_base64 else ""
            
            # Obtener número de tableros
            num_tableros = len(imagenes_base64)
            
            # Actualizar la optimización
            piezas_texto = "\n".join([
                f"{p['nombre']},{p['ancho']},{p['alto']},{p['cantidad']}" 
                for p in piezas_con_nombre
            ])
            
            optimizacion.ancho_tablero = ancho
            optimizacion.alto_tablero = alto
            optimizacion.unidad_medida = unidad
            optimizacion.piezas = piezas_texto
            optimizacion.aprovechamiento_total = aprovechamiento
            optimizacion.permitir_rotacion = permitir_rotacion
            optimizacion.margen_corte = margen_corte_cm
            optimizacion.material = material_seleccionado
            optimizacion.precio_tablero = precio_tablero
            optimizacion.mano_obra = mano_obra
            optimizacion.num_tableros = num_tableros
            optimizacion.cliente = tablero_form.cleaned_data.get('cliente')
            optimizacion.proyecto = tablero_form.cleaned_data.get('proyecto')
            optimizacion.save()

            numero_lista = calcular_numero_lista(request.user, optimizacion.id)
            persistir_resultado_optimizacion(
                optimizacion,
                imagenes_base64,
                info_desperdicio,
                aprovechamiento,
                numero_lista=numero_lista,
            )

            messages.success(request, f"✅ Optimización actualizada exitosamente. Aprovechamiento: {aprovechamiento:.2f}%")

            contexto = preparar_contexto_resultado(
                optimizacion,
                imagenes_base64,
                info_desperdicio,
            )
            contexto['numero_lista'] = numero_lista

            return render(request, "cutless/resultado.html", contexto)
        else:
            if not tablero_form.is_valid():
                messages.error(request, "❌ Error en las dimensiones del tablero.")
            if not pieza_formset.is_valid():
                messages.error(request, "❌ Error en los datos de las piezas.")
    else:
        # Cargar datos existentes en el formulario
        unidad_opt = getattr(optimizacion, 'unidad_medida', 'cm') or 'cm'
        ancho_mostrar = round(convertir_desde_cm(optimizacion.ancho_tablero, unidad_opt), 2)
        alto_mostrar = round(convertir_desde_cm(optimizacion.alto_tablero, unidad_opt), 2)
        
        # Crear formulario con datos iniciales
        initial_tablero = {
            'unidad_medida': unidad_opt,
            'ancho': ancho_mostrar,
            'alto': alto_mostrar,
            'permitir_rotacion': getattr(optimizacion, 'permitir_rotacion', True),
            'margen_corte': round(getattr(optimizacion, 'margen_corte', 0.3) * 10, 1),  # Convertir de cm a mm
            'material': getattr(optimizacion, 'material', None),
            'precio_tablero': getattr(optimizacion, 'precio_tablero', None),
            'mano_obra': getattr(optimizacion, 'mano_obra', 0),
            'cliente': getattr(optimizacion, 'cliente', None),
            'proyecto': getattr(optimizacion, 'proyecto', None),
        }
        tablero_form = TableroForm(initial=initial_tablero, user=request.user)
        
        # Cargar piezas existentes
        piezas_data = []
        for linea in optimizacion.piezas.splitlines():
            if linea.strip():
                partes = linea.split(',')
                if len(partes) == 4:
                    nombre, ancho, alto, cantidad = partes
                    # Convertir dimensiones de pieza a la unidad del tablero
                    ancho_cm = float(ancho.strip())
                    alto_cm = float(alto.strip())
                    ancho_mostrar = round(convertir_desde_cm(ancho_cm, unidad_opt), 2)
                    alto_mostrar = round(convertir_desde_cm(alto_cm, unidad_opt), 2)
                    piezas_data.append({
                        'nombre': nombre.strip(),
                        'ancho': ancho_mostrar,
                        'alto': alto_mostrar,
                        'cantidad': int(cantidad.strip())
                    })
        
        # Crear formset con datos iniciales
        # El formset ya tiene extra=1, así que solo pasamos las piezas existentes
        # El formset automáticamente agregará 1 formulario vacío adicional
        pieza_formset = PiezaFormSet(initial=piezas_data)
        
        # Preparar datos de materiales para JavaScript
        import json
        materiales_data = {}
        for material in Material.objects.filter(
            Q(usuario=request.user) | Q(es_predefinido=True)
        ):
            materiales_data[str(material.pk)] = {
                'precio': float(material.precio) if material.precio else None,
                'nombre': material.nombre,
                'ancho': float(material.ancho) if material.ancho else None,
                'alto': float(material.alto) if material.alto else None,
                'unidad_medida': material.unidad_medida if material.unidad_medida else 'cm'
            }
        materiales_data_json = json.dumps(materiales_data)
    
    return render(request, "cutless/editar_optimizacion.html", {
        "tablero_form": tablero_form,
        "pieza_formset": pieza_formset,
        "optimizacion": optimizacion,
        "materiales_data_json": materiales_data_json
    })

def index(request):
    # Si el usuario es admin, redirigir directo al dashboard de administración
    if request.user.is_superuser or (hasattr(request.user, 'perfil') and request.user.perfil.rol == 'admin'):
        return redirect('usuarios:admin_dashboard')

    # Limpiar mensajes antiguos al cargar el formulario por primera vez
    if request.method == "GET":
        storage = messages.get_messages(request)
        storage.used = True
    
    PiezaFormSet = formset_factory(PiezaForm, extra=1, max_num=20, validate_max=True)

    if request.method == "POST":
        tablero_form = TableroForm(request.POST, user=request.user)
        pieza_formset = PiezaFormSet(request.POST)

        if tablero_form.is_valid() and pieza_formset.is_valid():
            # Obtener unidad seleccionada
            unidad = tablero_form.cleaned_data.get("unidad_medida", "cm")
            
            # Obtener valores en la unidad del usuario
            ancho_usuario = tablero_form.cleaned_data["ancho"]
            alto_usuario = tablero_form.cleaned_data["alto"]
            
            # Convertir a cm para cálculos internos (mantener decimales)
            ancho = convertir_a_cm(ancho_usuario, unidad)
            alto = convertir_a_cm(alto_usuario, unidad)

            permitir_rotacion = tablero_form.cleaned_data.get('permitir_rotacion', True)

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
                        
                        # Convertir piezas a cm para validación y cálculos (mantener decimales)
                        pieza_ancho_cm = convertir_a_cm(pieza_ancho, unidad)
                        pieza_alto_cm = convertir_a_cm(pieza_alto, unidad)
                        
                        if not pieza_cabe_en_tablero(
                            pieza_ancho_cm, pieza_alto_cm, ancho, alto,
                            permitir_rotacion=permitir_rotacion,
                        ):
                            simbolo = obtener_simbolo_unidad(unidad)
                            sug = ''
                            if (not permitir_rotacion and pieza_cabe_en_tablero(
                                pieza_ancho_cm, pieza_alto_cm, ancho, alto,
                                permitir_rotacion=True,
                            )):
                                sug = (
                                    ' Prueba activar «Rotación automática»: con rotación sí cabe como una sola pieza.'
                                )
                            messages.error(
                                request,
                                f"❌ La pieza «{nombre}» ({pieza_ancho}×{pieza_alto} {simbolo}) NO CABE "
                                f"como placas rectangulares en el tablero ({ancho_usuario}×{alto_usuario} {simbolo})."
                                f"{sug}"
                            )
                            return render(request, "cutless/index.html", {
                                "tablero_form": tablero_form,
                                "pieza_formset": pieza_formset,
                                "materiales_data_json": _materiales_data_json_index(request.user),
                            })
                        
                        # Guardar piezas en cm para cálculos
                        piezas.append((pieza_ancho_cm, pieza_alto_cm, cantidad))
                        piezas_con_nombre.append({
                            'nombre': nombre,
                            'ancho': pieza_ancho,  # Guardar valor original para mostrar
                            'alto': pieza_alto,  # Guardar valor original para mostrar
                            'cantidad': cantidad
                        })
            
            # Validar que haya al menos una pieza
            if not piezas:
                messages.error(request, "❌ Debes agregar al menos una pieza con dimensiones válidas.")
                # Preparar datos de materiales para JavaScript
                import json
                materiales_data = {}
                for material in Material.objects.filter(
                    Q(usuario=request.user) | Q(es_predefinido=True)
                ):
                    materiales_data[str(material.pk)] = {
                        'precio': float(material.precio) if material.precio else None,
                        'nombre': material.nombre
                    }
                materiales_data_json = json.dumps(materiales_data)
                return render(request, "cutless/index.html", {
                    "tablero_form": TableroForm(user=request.user),
                    "pieza_formset": pieza_formset,
                    "materiales_data_json": materiales_data_json
                })

            margen_corte_mm = tablero_form.cleaned_data.get('margen_corte') or 3  # Siempre en mm, default 3
            # Convertir margen de corte de mm a cm (el sistema trabaja en cm)
            margen_corte_cm = margen_corte_mm / 10.0

            # Obtener datos de costos
            material_seleccionado = tablero_form.cleaned_data.get('material')
            precio_tablero = tablero_form.cleaned_data.get('precio_tablero')
            mano_obra = tablero_form.cleaned_data.get('mano_obra') or 0

            # Limitar acceso a la sección de costos según el permiso del usuario
            tiene_permiso_costos = (request.user.is_authenticated and hasattr(request.user, 'perfil') and request.user.perfil.puede_ver_historial_costos)
            if not tiene_permiso_costos:
                material_seleccionado = None
                precio_tablero = None
                mano_obra = 0
                cliente_seleccionado = None
                proyecto_seleccionado = None
            else:
                # Si se seleccionó un material y no hay precio manual, usar el del material
                if material_seleccionado and not precio_tablero:
                    precio_tablero = material_seleccionado.precio
                cliente_seleccionado = tablero_form.cleaned_data.get('cliente')
                proyecto_seleccionado = tablero_form.cleaned_data.get('proyecto')

            # Extraer nombres de piezas para colores consistentes
            nombres_piezas = [p['nombre'] for p in piezas_con_nombre]
            
            # Generar TODAS las imágenes, aprovechamiento Y desperdicio
            imagenes_base64, aprovechamiento, info_desperdicio = generar_grafico(
                piezas, ancho, alto, unidad, 
                permitir_rotacion=permitir_rotacion, 
                margen_corte=margen_corte_cm,
                nombres_piezas=nombres_piezas
            )

            ncol = info_desperdicio.get('num_piezas_colocadas') or 0
            nsol = info_desperdicio.get('num_piezas_solicitadas') or 0
            if nsol > 0 and ncol == 0:
                warn = mensaje_advertencia_piezas_no_colocadas(info_desperdicio, unidad)
                messages.error(request, warn or '❌ No se pudo colocar ninguna pieza en el tablero.')
                return render(request, "cutless/index.html", {
                    "tablero_form": tablero_form,
                    "pieza_formset": pieza_formset,
                    "materiales_data_json": _materiales_data_json_index(request.user),
                })

            warn_omitidas = mensaje_advertencia_piezas_no_colocadas(info_desperdicio, unidad)
            if warn_omitidas:
                messages.warning(request, warn_omitidas)
            
            # Usar la primera imagen para vista previa
            imagen_principal = imagenes_base64[0] if imagenes_base64 else ""
            
            # Obtener número de tableros
            num_tableros = len(imagenes_base64)

            # Guardar en BD (ahora con nombres y costos)
            piezas_texto = "\n".join([
                f"{p['nombre']},{p['ancho']},{p['alto']},{p['cantidad']}" 
                for p in piezas_con_nombre
            ])
            
            optimizacion = Optimizacion.objects.create(
                usuario=request.user,
                ancho_tablero=ancho,  # Guardado en cm
                alto_tablero=alto,  # Guardado en cm
                unidad_medida=unidad,  # Guardar unidad original
                piezas=piezas_texto,
                aprovechamiento_total=aprovechamiento,
                permitir_rotacion=permitir_rotacion,
                margen_corte=margen_corte_cm,
                material=material_seleccionado,
                precio_tablero=precio_tablero,
                mano_obra=mano_obra,
                num_tableros=num_tableros,
                cliente=cliente_seleccionado,
                proyecto=proyecto_seleccionado
            )

            numero_lista = calcular_numero_lista(request.user, optimizacion.id)
            persistir_resultado_optimizacion(
                optimizacion,
                imagenes_base64,
                info_desperdicio,
                aprovechamiento,
                numero_lista=numero_lista,
            )

            contexto = preparar_contexto_resultado(
                optimizacion,
                imagenes_base64,
                info_desperdicio,
            )
            contexto['numero_lista'] = numero_lista
            
            # Enviar notificación de optimización completada (cuando se crea desde index)
            enviar_notificacion(
                request,
                'optimizacion_completada',
                'Optimización Completada',
                f'Tu optimización #{numero_lista} ha sido completada exitosamente con un aprovechamiento del {aprovechamiento:.2f}%.',
                {'optimizacion_id': optimizacion.id, 'aprovechamiento': aprovechamiento}
            )
            
            return render(request, "cutless/resultado.html", contexto)
        else:
            # Mostrar errores de validación
            if not tablero_form.is_valid():
                messages.error(request, "❌ Error en las dimensiones del tablero.")
            if not pieza_formset.is_valid():
                messages.error(request, "❌ Error en los datos de las piezas.")
            
            # Preparar datos de materiales para JavaScript (necesario cuando hay errores)
            import json
            materiales_data = {}
            for material in Material.objects.filter(
                Q(usuario=request.user) | Q(es_predefinido=True)
            ):
                materiales_data[str(material.pk)] = {
                    'precio': float(material.precio) if material.precio else None,
                    'nombre': material.nombre
                }
            materiales_data_json = json.dumps(materiales_data)
    else:
        # Preparar valores iniciales desde el perfil del usuario (solo optimización)
        initial_data = {}
        try:
            # Refrescar el perfil desde la base de datos para obtener los valores más recientes
            perfil = request.user.perfil
            perfil.refresh_from_db()
            
            # Unidad de medida predeterminada
            if perfil.unidad_medida_predeterminada:
                # Normalizar unidad para compatibilidad
                unidad = perfil.unidad_medida_predeterminada
                if unidad == 'pulgadas':
                    unidad = 'in'
                initial_data['unidad_medida'] = unidad
            
            # Margen de corte predeterminado (convertir de cm a mm)
            # CORREGIDO: Siempre establecer el margen si existe en el perfil
            # Asegurar conversión correcta de Decimal a float
            if perfil.margen_corte_predeterminado is not None:
                # Convertir Decimal a float si es necesario
                if isinstance(perfil.margen_corte_predeterminado, Decimal):
                    margen_cm = float(perfil.margen_corte_predeterminado)
                else:
                    margen_cm = float(perfil.margen_corte_predeterminado)
                # Convertir de cm a mm y asegurar que sea un número válido
                margen_mm = margen_cm * 10.0
                margen_mm_redondeado = round(margen_mm, 1)
                # Si es un entero, guardar como entero para evitar decimales innecesarios
                if margen_mm_redondeado == int(margen_mm_redondeado):
                    initial_data['margen_corte'] = int(margen_mm_redondeado)
                else:
                    initial_data['margen_corte'] = margen_mm_redondeado
                # Debug: verificar que el valor se está estableciendo
                if settings.DEBUG:
                    print(f"DEBUG: Margen de corte establecido en initial_data: {initial_data['margen_corte']} mm (desde {margen_cm} cm)")
            
            # Rotación automática predeterminada
            if perfil.rotacion_automatica_predeterminada is not None:
                initial_data['permitir_rotacion'] = perfil.rotacion_automatica_predeterminada
                
        except AttributeError:
            # Si el usuario no tiene perfil, usar valores por defecto
            pass
        
        # Crear formulario con valores iniciales
        # CORREGIDO: Siempre pasar initial_data, incluso si está vacío, para que el formulario pueda aplicar valores predeterminados
        tablero_form = TableroForm(initial=initial_data, user=request.user)
        pieza_formset = PiezaFormSet()
        
        # Preparar datos de materiales para JavaScript
        import json
        materiales_data = {}
        for material in Material.objects.filter(
            Q(usuario=request.user) | Q(es_predefinido=True)
        ):
            materiales_data[str(material.pk)] = {
                'precio': float(material.precio) if material.precio else None,
                'nombre': material.nombre,
                'ancho': float(material.ancho) if material.ancho else None,
                'alto': float(material.alto) if material.alto else None,
                'unidad_medida': material.unidad_medida if material.unidad_medida else 'cm'
            }
        materiales_data_json = json.dumps(materiales_data)

    return render(request, "cutless/index.html", {
        "tablero_form": tablero_form,
        "pieza_formset": pieza_formset,
        "materiales_data_json": materiales_data_json
    })

def resultado_view(request, pk=None):
    """
    Vista para mostrar el resultado de una optimización.
    Si pk está presente, muestra una optimización existente.
    Si es POST, procesa una nueva optimización.
    """
    # Si hay un pk, mostrar optimización existente
    if pk:
        optimizacion = get_object_or_404(Optimizacion, pk=pk, usuario=request.user)
        numero_lista = calcular_numero_lista(request.user, optimizacion.id)
        imagenes_base64, _, info_desperdicio = obtener_resultado_optimizacion(
            optimizacion,
            numero_lista=numero_lista,
            persistir_si_falta=True,
        )
        contexto = preparar_contexto_resultado(
            optimizacion,
            imagenes_base64,
            info_desperdicio,
        )
        contexto['numero_lista'] = numero_lista
        return render(request, "cutless/resultado.html", contexto)
    
    if request.method == "POST":
        piezas_texto = request.POST.get("piezas") or ""

        unidad_resultado = request.POST.get('unidad_medida', 'cm')
        if not unidad_resultado:
            unidad_resultado = 'cm'

        permitir_rotacion = request.POST.get('permitir_rotacion', 'true').lower() == 'true'

        ancho_usuario = float(request.POST.get("ancho_tablero"))
        alto_usuario = float(request.POST.get("alto_tablero"))
        ancho_cm = convertir_a_cm(ancho_usuario, unidad_resultado)
        alto_cm = convertir_a_cm(alto_usuario, unidad_resultado)

        piezas = []
        piezas_con_nombre = []
        for linea in piezas_texto.strip().splitlines():
            partes = linea.split(",")
            if len(partes) == 4:  # Con nombre
                nombre, w, h, c = partes
                wf, hf = float(w), float(h)
                cn = int(c)
                nombre = nombre.strip()
                w_cm = convertir_a_cm(wf, unidad_resultado)
                h_cm = convertir_a_cm(hf, unidad_resultado)
                if not pieza_cabe_en_tablero(w_cm, h_cm, ancho_cm, alto_cm, permitir_rotacion):
                    simbolo = obtener_simbolo_unidad(unidad_resultado)
                    sug = ''
                    if not permitir_rotacion and pieza_cabe_en_tablero(w_cm, h_cm, ancho_cm, alto_cm, True):
                        sug = (
                            ' Prueba activar «Rotación automática»: con rotación sí cabe como una sola pieza.'
                        )
                    messages.error(
                        request,
                        f"❌ La pieza «{nombre}» ({wf}×{hf} {simbolo}) NO CABE en el tablero "
                        f"({ancho_usuario}×{alto_usuario} {simbolo}).{sug}"
                    )
                    return redirect('cutless:index')
                piezas.append((w_cm, h_cm, cn))
                piezas_con_nombre.append({
                    'nombre': nombre,
                    'ancho': wf,
                    'alto': hf,
                    'cantidad': cn
                })
            else:  # Sin nombre
                w, h, c = partes
                wf, hf = float(w), float(h)
                cn = int(c)
                lbl = f"Pieza {len(piezas_con_nombre) + 1}"
                w_cm = convertir_a_cm(wf, unidad_resultado)
                h_cm = convertir_a_cm(hf, unidad_resultado)
                if not pieza_cabe_en_tablero(w_cm, h_cm, ancho_cm, alto_cm, permitir_rotacion):
                    simbolo = obtener_simbolo_unidad(unidad_resultado)
                    messages.error(
                        request,
                        f"❌ La pieza {lbl} ({wf}×{hf} {simbolo}) NO CABE en el tablero "
                        f"({ancho_usuario}×{alto_usuario} {simbolo})."
                    )
                    return redirect('cutless:index')
                piezas.append((w_cm, h_cm, cn))
                piezas_con_nombre.append({
                    'nombre': lbl,
                    'ancho': wf,
                    'alto': hf,
                    'cantidad': cn
                })

        # Obtener parámetros de rotación y margen de corte (valores por defecto para compatibilidad)
        margen_corte_str = request.POST.get('margen_corte', '') or '3'
        margen_corte_mm = float(margen_corte_str)  # Siempre en mm, default 3
        margen_corte_cm = margen_corte_mm / 10.0  # Convertir de mm a cm
        
        # Obtener datos de costos (si existen)
        material_id = request.POST.get('material')
        material_seleccionado = None
        if material_id:
            # Intentar obtener material del usuario primero, luego predefinido
            material_seleccionado = Material.objects.filter(
                pk=material_id
            ).filter(
                Q(usuario=request.user) | Q(es_predefinido=True)
            ).first()
        
        precio_tablero = request.POST.get('precio_tablero')
        if precio_tablero:
            precio_tablero = Decimal(precio_tablero)
        elif material_seleccionado and material_seleccionado.precio:
            precio_tablero = material_seleccionado.precio
        else:
            precio_tablero = None
        
        mano_obra = request.POST.get('mano_obra')
        if mano_obra:
            mano_obra = Decimal(mano_obra)
        else:
            mano_obra = Decimal('0.00')
        
        # Extraer nombres de piezas para colores consistentes
        nombres_piezas = [p['nombre'] for p in piezas_con_nombre]
        
        # Generar TODAS las imágenes con info de desperdicio (piezas y tablero en cm)
        imagenes_base64, aprovechamiento, info_desperdicio = generar_grafico(
            piezas, ancho_cm, alto_cm, unidad_resultado,
            permitir_rotacion=permitir_rotacion,
            margen_corte=margen_corte_cm,
            nombres_piezas=nombres_piezas
        )

        ncol = info_desperdicio.get('num_piezas_colocadas') or 0
        nsol = info_desperdicio.get('num_piezas_solicitadas') or 0
        if nsol > 0 and ncol == 0:
            warn = mensaje_advertencia_piezas_no_colocadas(info_desperdicio, unidad_resultado)
            messages.error(request, warn or '❌ No se pudo colocar ninguna pieza en el tablero.')
            return redirect('cutless:index')

        warn_omitidas = mensaje_advertencia_piezas_no_colocadas(info_desperdicio, unidad_resultado)
        if warn_omitidas:
            messages.warning(request, warn_omitidas)

        imagen_principal = imagenes_base64[0] if imagenes_base64 else ""
        
        num_tableros = len(imagenes_base64)

        optimizacion = Optimizacion.objects.create(
            usuario=request.user,
            ancho_tablero=ancho_cm,
            alto_tablero=alto_cm,
            unidad_medida=unidad_resultado,
            piezas=piezas_texto,
            aprovechamiento_total=aprovechamiento,
            permitir_rotacion=permitir_rotacion,
            margen_corte=margen_corte_cm,
            material=material_seleccionado,
            precio_tablero=precio_tablero,
            mano_obra=mano_obra,
            num_tableros=num_tableros
        )

        numero_lista = calcular_numero_lista(request.user, optimizacion.id)
        persistir_resultado_optimizacion(
            optimizacion,
            imagenes_base64,
            info_desperdicio,
            aprovechamiento,
            numero_lista=numero_lista,
        )

        enviar_notificacion(
            request,
            'optimizacion_completada',
            'Optimización Completada',
            f'Tu optimización #{numero_lista} ha sido completada exitosamente con un aprovechamiento del {aprovechamiento:.2f}%.',
            {'optimizacion_id': optimizacion.id, 'aprovechamiento': aprovechamiento}
        )

        contexto = preparar_contexto_resultado(
            optimizacion,
            imagenes_base64,
            info_desperdicio,
        )
        contexto['numero_lista'] = numero_lista
        return render(request, "cutless/resultado.html", contexto)

def duplicar_optimizacion(request, pk):
    """
    Duplica una optimización existente y carga sus datos en el formulario.
    """
    optimizacion = get_object_or_404(Optimizacion, pk=pk, usuario=request.user)
    
    # Obtener el ordenamiento actual desde los parámetros GET (si existe)
    ordenar_por = request.GET.get('ordenar_por', 'fecha_desc')
    
    # Calcular el número de visualización igual que en historial
    todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user)
    
    # Aplicar filtros si existen (para mantener consistencia)
    solo_favoritos = request.GET.get('solo_favoritos', '').strip()
    if solo_favoritos == 'true':
        todas_optimizaciones = todas_optimizaciones.filter(favorito=True)
    
    nombre_pieza = request.GET.get('nombre_pieza', '').strip()
    if nombre_pieza:
        todas_optimizaciones = todas_optimizaciones.filter(piezas__icontains=nombre_pieza)
    
    # Aplicar el mismo ordenamiento que se usa en historial
    if ordenar_por == 'fecha_desc':
        todas_optimizaciones = todas_optimizaciones.order_by('-fecha')
    elif ordenar_por == 'fecha_asc':
        todas_optimizaciones = todas_optimizaciones.order_by('fecha')
    elif ordenar_por == 'aprovechamiento_desc':
        todas_optimizaciones = todas_optimizaciones.order_by('-aprovechamiento_total')
    elif ordenar_por == 'aprovechamiento_asc':
        todas_optimizaciones = todas_optimizaciones.order_by('aprovechamiento_total')
    else:
        todas_optimizaciones = todas_optimizaciones.order_by('-fecha')
    
    total_optimizaciones = todas_optimizaciones.count()
    es_descendente = ordenar_por in ['fecha_desc', 'aprovechamiento_desc']
    
    # Encontrar la posición de esta optimización en la lista
    numero_mostrado = optimizacion.id  # Por defecto usar el ID real
    for idx, opt in enumerate(todas_optimizaciones, start=1):
        if opt.id == optimizacion.id:
            # Calcular número de lista según el ordenamiento (igual que en historial)
            if es_descendente:
                numero_mostrado = total_optimizaciones - idx + 1
            else:
                numero_mostrado = idx
            break
    
    # Parsear las piezas guardadas
    piezas_data = []
    for linea in optimizacion.piezas.splitlines():
        partes = linea.split(',')
        if len(partes) == 4:  # Con nombre
            nombre, ancho, alto, cantidad = partes
            piezas_data.append({
                'nombre': nombre.strip(),
                'ancho': float(ancho.strip()),  # Cambiado a float para manejar decimales
                'alto': float(alto.strip()),    # Cambiado a float para manejar decimales
                'cantidad': int(cantidad.strip())
            })
        else:  # Sin nombre (formato antiguo)
            ancho, alto, cantidad = partes
            piezas_data.append({
                'nombre': '',
                'ancho': float(ancho.strip()),  # Cambiado a float para manejar decimales
                'alto': float(alto.strip()),    # Cambiado a float para manejar decimales
                'cantidad': int(cantidad.strip())
            })
    
    # Crear formset con los datos de la optimización
    PiezaFormSet = formset_factory(PiezaForm, extra=0, max_num=20)
    
    # Obtener unidad de la optimización (o 'cm' por defecto para datos antiguos)
    unidad_original = getattr(optimizacion, 'unidad_medida', 'cm')
    
    # Convertir dimensiones de cm a la unidad original para mostrar
    ancho_mostrar = convertir_desde_cm(optimizacion.ancho_tablero, unidad_original)
    alto_mostrar = convertir_desde_cm(optimizacion.alto_tablero, unidad_original)
    
    # Convertir piezas de cm a la unidad original
    for pieza in piezas_data:
        pieza['ancho'] = round(convertir_desde_cm(float(pieza['ancho']), unidad_original), 2)
        pieza['alto'] = round(convertir_desde_cm(float(pieza['alto']), unidad_original), 2)
    
    # Crear formularios con datos prellenados
    tablero_form = TableroForm(initial={
        'ancho': ancho_mostrar,
        'alto': alto_mostrar,
        'unidad_medida': unidad_original
    })
    
    pieza_formset = PiezaFormSet(initial=piezas_data)
    
    # Usar el número de visualización calculado (igual que se muestra en historial)
    # Esto asegura que el mensaje muestre el mismo número que se ve en la pantalla
    messages.info(request, f"📋 Cargando datos de la optimización #{numero_mostrado}. Puedes modificarlos antes de calcular.")
    
    return render(request, "cutless/index.html", {
        "tablero_form": tablero_form,
        "pieza_formset": pieza_formset,
        "duplicando": True,
        "optimizacion_original": optimizacion
    })

