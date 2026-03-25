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
from django.http import FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.utils import timezone

# Imports del proyecto
from opti import settings
from .forms import TableroForm, PiezaForm, MaterialForm, ClienteForm, PresupuestoForm, ProyectoForm, PlantillaForm
from .models import Optimizacion, Material, Cliente, Presupuesto, Proyecto, Plantilla
from .utils import (
    convertir_a_cm, convertir_desde_cm, generar_excel, generar_grafico,
    generar_grafico_aprovechamiento, generar_grafico_desperdicio, generar_pdf,
    generar_excel_resumen_desperdicio, generar_pdf_resumen_desperdicio,
    obtener_simbolo_area, obtener_simbolo_unidad
)
from .utils_notificaciones import enviar_notificacion

@login_required
def index(request):
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
                        
                        # Validar que la pieza no sea más grande que el tablero (en cm)
                        if pieza_ancho_cm > ancho or pieza_alto_cm > alto:
                            simbolo = obtener_simbolo_unidad(unidad)
                            messages.error(
                                request, 
                                f"❌ La pieza '{nombre}' ({pieza_ancho}x{pieza_alto} {simbolo}) NO CABE en el tablero ({ancho_usuario}x{alto_usuario} {simbolo})."
                            )
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
                            return render(request, "opticut/index.html", {
                                "tablero_form": TableroForm(user=request.user),
                                "pieza_formset": pieza_formset,
                                "materiales_data_json": materiales_data_json
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
                return render(request, "opticut/index.html", {
                    "tablero_form": TableroForm(user=request.user),
                    "pieza_formset": pieza_formset,
                    "materiales_data_json": materiales_data_json
                })

            # Obtener parámetros de rotación y margen de corte
            permitir_rotacion = tablero_form.cleaned_data.get('permitir_rotacion', True)
            margen_corte_mm = tablero_form.cleaned_data.get('margen_corte') or 3  # Siempre en mm, default 3
            # Convertir margen de corte de mm a cm (el sistema trabaja en cm)
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
            
            # Generar TODAS las imágenes, aprovechamiento Y desperdicio
            imagenes_base64, aprovechamiento, info_desperdicio = generar_grafico(
                piezas, ancho, alto, unidad, 
                permitir_rotacion=permitir_rotacion, 
                margen_corte=margen_corte_cm,
                nombres_piezas=nombres_piezas
            )
            
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

            # Guardar la primera imagen en el FileField
            if imagen_principal:
                image_data = base64.b64decode(imagen_principal)
                file = ContentFile(image_data, name=f"optimizacion_{request.user.username}_{optimizacion.id}.png")
                optimizacion.imagen.save(f"optimizacion_{request.user.username}_{optimizacion.id}.png", file)
            
            # Calcular el número de lista para el PDF (basado en orden por fecha descendente por defecto)
            # Obtener todas las optimizaciones ordenadas por fecha descendente (igual que en historial)
            todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user).order_by('-fecha')
            total_optimizaciones = todas_optimizaciones.count()
            
            # Encontrar la posición real de esta optimización en la lista ordenada
            # Para orden descendente: primera = número más alto (total_optimizaciones)
            for idx, opt in enumerate(todas_optimizaciones, start=1):
                if opt.id == optimizacion.id:
                    # Para orden descendente: numero = total - idx + 1
                    numero_lista = total_optimizaciones - idx + 1
                    break
            else:
                # Si no se encuentra (no debería pasar), usar el total como fallback
                numero_lista = total_optimizaciones
            
            # Generar UN SOLO PDF con todos los tableros usando el número de lista correcto
            try:
                pdf_path = generar_pdf(optimizacion, imagenes_base64, numero_lista=numero_lista)
            except Exception as e:
                messages.warning(request, f"⚠️ PDF no generado: {str(e)}")
                pdf_path = None
            
            # Obtener unidad de la optimización
            unidad = getattr(optimizacion, 'unidad_medida', 'cm') or 'cm'
            
            # Convertir áreas de cm² a la unidad del usuario para mostrar
            # Para áreas: si 1 cm = X unidades, entonces 1 cm² = X² unidades²
            simbolo_area = obtener_simbolo_area(unidad)
            
            # Factor de conversión para áreas (factor lineal al cuadrado)
            factor_lineal = convertir_desde_cm(1, unidad)  # Cuántas unidades hay en 1 cm
            factor_area = factor_lineal ** 2  # Factor para áreas
            
            area_usada_mostrar = round(info_desperdicio['area_usada_total'] * factor_area, 2)
            desperdicio_mostrar = round(info_desperdicio['desperdicio_total'] * factor_area, 2)
            
            # Convertir info de tableros
            info_tableros_convertida = []
            for info in info_desperdicio['info_tableros']:
                area_usada_tab = round(info['area_usada'] * factor_area, 2)
                desperdicio_tab = round(info['desperdicio'] * factor_area, 2)
                info_tableros_convertida.append({
                    **info,
                    'area_usada': area_usada_tab,
                    'desperdicio': desperdicio_tab,
                })
            
            info_desperdicio_mostrar = {
                **info_desperdicio,
                'area_usada_total': area_usada_mostrar,
                'desperdicio_total': desperdicio_mostrar,
                'info_tableros': info_tableros_convertida,
            }
            
            # Combinar imágenes con información de tableros para asegurar enumeración correcta
            tableros_con_imagenes = []
            for idx, (img, info) in enumerate(zip(imagenes_base64, info_tableros_convertida), start=1):
                tableros_con_imagenes.append({
                    'numero': info['numero'],
                    'imagen': img,
                    'info': info
                })
            
            # Calcular costos
            costo_total = optimizacion.get_costo_total()
            costo_material = None
            if precio_tablero:
                costo_material = Decimal(str(num_tableros)) * precio_tablero
            
            # Enviar notificación de optimización completada (cuando se crea desde index)
            enviar_notificacion(
                request,
                'optimizacion_completada',
                'Optimización Completada',
                f'Tu optimización #{numero_lista} ha sido completada exitosamente con un aprovechamiento del {aprovechamiento:.2f}%.',
                {'optimizacion_id': optimizacion.id, 'aprovechamiento': aprovechamiento}
            )
            
            return render(request, "opticut/resultado.html", {
                "imagen": imagen_principal,
                "imagenes": imagenes_base64,
                "optimizacion": optimizacion,
                "pdf_path": pdf_path,
                "num_tableros": len(imagenes_base64),
                "piezas_con_nombre": piezas_con_nombre,
                "info_desperdicio": info_desperdicio_mostrar,
                "tableros_con_imagenes": tableros_con_imagenes,
                "numero_lista": numero_lista,  # Pasar número de lista para usar en descarga PNG
                "unidad_medida": unidad,
                "simbolo_area": simbolo_area,
                "costo_total": costo_total,
                "costo_material": costo_material,
                "precio_tablero": precio_tablero,
                "mano_obra": mano_obra,
            })
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

    return render(request, "opticut/index.html", {
        "tablero_form": tablero_form,
        "pieza_formset": pieza_formset,
        "materiales_data_json": materiales_data_json
    })


@login_required
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
                        
                        if pieza_ancho_cm > ancho or pieza_alto_cm > alto:
                            simbolo = obtener_simbolo_unidad(unidad)
                            messages.error(
                                request, 
                                f"❌ La pieza '{nombre}' ({pieza_ancho}x{pieza_alto} {simbolo}) NO CABE en el tablero ({ancho_usuario}x{alto_usuario} {simbolo})."
                            )
                            return render(request, "opticut/editar_optimizacion.html", {
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
                return render(request, "opticut/editar_optimizacion.html", {
                    "tablero_form": tablero_form,
                    "pieza_formset": pieza_formset,
                    "optimizacion": optimizacion
                })
            
            # Obtener parámetros de rotación y margen de corte
            permitir_rotacion = tablero_form.cleaned_data.get('permitir_rotacion', True)
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
            
            # Actualizar imagen
            if imagen_principal:
                image_data = base64.b64decode(imagen_principal)
                file = ContentFile(image_data, name=f"optimizacion_{request.user.username}_{optimizacion.id}.png")
                optimizacion.imagen.save(f"optimizacion_{request.user.username}_{optimizacion.id}.png", file, save=False)
            
            optimizacion.save()
            
            # Regenerar PDF
            todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user).order_by('-fecha')
            total_optimizaciones = todas_optimizaciones.count()
            for idx, opt in enumerate(todas_optimizaciones, start=1):
                if opt.id == optimizacion.id:
                    numero_lista = total_optimizaciones - idx + 1
                    break
            else:
                numero_lista = total_optimizaciones
            
            try:
                pdf_path = generar_pdf(optimizacion, imagenes_base64, numero_lista=numero_lista)
            except Exception as e:
                messages.warning(request, f"⚠️ PDF no generado: {str(e)}")
                pdf_path = None
            
            messages.success(request, f"✅ Optimización actualizada exitosamente. Aprovechamiento: {aprovechamiento:.2f}%")
            
            # Preparar datos para mostrar
            unidad_opt = getattr(optimizacion, 'unidad_medida', 'cm') or 'cm'
            simbolo_area = obtener_simbolo_area(unidad_opt)
            factor_lineal = convertir_desde_cm(1, unidad_opt)
            factor_area = factor_lineal ** 2
            
            area_usada_mostrar = round(info_desperdicio['area_usada_total'] * factor_area, 2)
            desperdicio_mostrar = round(info_desperdicio['desperdicio_total'] * factor_area, 2)
            
            info_tableros_convertida = []
            for info in info_desperdicio['info_tableros']:
                area_usada_tab = round(info['area_usada'] * factor_area, 2)
                desperdicio_tab = round(info['desperdicio'] * factor_area, 2)
                info_tableros_convertida.append({
                    **info,
                    'area_usada': area_usada_tab,
                    'desperdicio': desperdicio_tab,
                })
            
            info_desperdicio_mostrar = {
                **info_desperdicio,
                'area_usada_total': area_usada_mostrar,
                'desperdicio_total': desperdicio_mostrar,
                'info_tableros': info_tableros_convertida,
            }
            
            tableros_con_imagenes = []
            for idx, (img, info) in enumerate(zip(imagenes_base64, info_tableros_convertida), start=1):
                tableros_con_imagenes.append({
                    'numero': info['numero'],
                    'imagen': img,
                    'info': info
                })
            
            # Calcular costos
            costo_total = optimizacion.get_costo_total()
            costo_material = None
            if precio_tablero:
                costo_material = Decimal(str(num_tableros)) * precio_tablero
            
            return render(request, "opticut/resultado.html", {
                "imagen": imagen_principal,
                "imagenes": imagenes_base64,
                "optimizacion": optimizacion,
                "pdf_path": pdf_path,
                "num_tableros": len(imagenes_base64),
                "piezas_con_nombre": piezas_con_nombre,
                "info_desperdicio": info_desperdicio_mostrar,
                "tableros_con_imagenes": tableros_con_imagenes,
                "numero_lista": numero_lista,
                "unidad_medida": unidad_opt,
                "simbolo_area": simbolo_area,
                "costo_total": costo_total,
                "costo_material": costo_material,
                "precio_tablero": precio_tablero,
                "mano_obra": mano_obra,
            })
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
    
    return render(request, "opticut/editar_optimizacion.html", {
        "tablero_form": tablero_form,
        "pieza_formset": pieza_formset,
        "optimizacion": optimizacion,
        "materiales_data_json": materiales_data_json
    })


@login_required
def historial(request):
    # Obtener TODAS las optimizaciones del usuario para calcular números absolutos
    todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user)
    total_absoluto = todas_optimizaciones.count()
    
    # Ordenamiento (aplicar a todas para calcular números correctos)
    ordenar_por = request.GET.get('ordenar_por', 'fecha_desc')
    
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
    
    # Determinar si el ordenamiento es descendente o ascendente
    es_descendente = ordenar_por in ['fecha_desc', 'aprovechamiento_desc']
    
    # Crear diccionario de ID -> número absoluto
    numeros_absolutos = {}
    for idx, opt in enumerate(todas_optimizaciones, start=1):
        if es_descendente:
            numeros_absolutos[opt.id] = total_absoluto - idx + 1
        else:
            numeros_absolutos[opt.id] = idx
    
    # Ahora aplicar filtros para mostrar
    optimizaciones = todas_optimizaciones
    
    # Filtro por favoritos
    solo_favoritos = request.GET.get('solo_favoritos', '').strip()
    if solo_favoritos == 'true':
        optimizaciones = optimizaciones.filter(favorito=True)
    
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
    
    # PAGINACIÓN
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    page = request.GET.get('page', 1)
    paginator = Paginator(optimizaciones, 12)  # 12 optimizaciones por página
    try:
        optimizaciones_page = paginator.page(page)
    except PageNotAnInteger:
        optimizaciones_page = paginator.page(1)
    except EmptyPage:
        optimizaciones_page = paginator.page(paginator.num_pages)

    optimizaciones_con_piezas = []
    for opt in optimizaciones_page:
        numero_mostrado = numeros_absolutos.get(opt.id, 0)
        piezas_procesadas = []
        for linea in opt.piezas.splitlines():
            if linea.strip():
                partes = linea.split(',')
                if len(partes) == 4:
                    piezas_procesadas.append({
                        'nombre': partes[0].strip(),
                        'ancho': partes[1].strip(),
                        'alto': partes[2].strip(),
                        'cantidad': partes[3].strip()
                    })
                elif len(partes) == 3:
                    piezas_procesadas.append({
                        'nombre': 'Pieza',
                        'ancho': partes[0].strip(),
                        'alto': partes[1].strip(),
                        'cantidad': partes[2].strip()
                    })
        unidad_opt = getattr(opt, 'unidad_medida', 'cm') or 'cm'
        ancho_mostrar = round(convertir_desde_cm(opt.ancho_tablero, unidad_opt), 2)
        alto_mostrar = round(convertir_desde_cm(opt.alto_tablero, unidad_opt), 2)
        optimizaciones_con_piezas.append({
            'optimizacion': opt,
            'piezas': piezas_procesadas,
            'numero': numero_mostrado,
            'ancho_mostrar': ancho_mostrar,
            'alto_mostrar': alto_mostrar,
            'unidad_medida': unidad_opt,
        })

    return render(request, 'opticut/historial.html', {
        'optimizaciones_con_piezas': optimizaciones_con_piezas,
        'nombre_pieza': nombre_pieza,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'ordenar_por': ordenar_por,
        'solo_favoritos': solo_favoritos,
        'total_sin_filtro': total_absoluto,
        'page_obj': optimizaciones_page,
        'paginator': paginator,
    })




@login_required
def borrar_historial(request):
    if request.method == "POST":
        optimizaciones = Optimizacion.objects.filter(usuario=request.user)
        count = optimizaciones.count()
        optimizaciones.delete()
        messages.success(request, f"Se eliminaron {count} optimizaciones del historial.")
        return redirect('opticut:historial')
    else:
        messages.error(request, "Operación no permitida.")
        return redirect('opticut:historial')


@login_required
def borrar_optimizacion(request, pk):
    """
    Elimina una optimización individual del usuario actual.
    """
    optimizacion = get_object_or_404(Optimizacion, pk=pk, usuario=request.user)
    todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user).order_by('-fecha')
    total_absoluto = todas_optimizaciones.count()
    numero_mostrado = None
    for idx, opt in enumerate(todas_optimizaciones, start=1):
        if opt.id == pk:
            numero_mostrado = total_absoluto - idx + 1
            break
    if numero_mostrado is None:
        numero_mostrado = pk

    if request.method == "POST":
        optimizacion.delete()
        messages.success(request, f"Optimización #{numero_mostrado} eliminada correctamente.")
        return redirect('opticut:historial')
    else:
        return render(request, 'opticut/eliminar_optimizacion.html', {
            'optimizacion': optimizacion,
            'numero_mostrado': numero_mostrado,
        })


@login_required
def descargar_pdf(request, pk):
    optimizacion = get_object_or_404(Optimizacion, pk=pk, usuario=request.user)
    
    # Obtener el ordenamiento actual desde los parámetros GET (si existe)
    ordenar_por = request.GET.get('ordenar_por', 'fecha_desc')
    
    # Aplicar el mismo ordenamiento que se usa en historial
    todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user)
    
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
    
    # Determinar si el ordenamiento es descendente o ascendente
    es_descendente = ordenar_por in ['fecha_desc', 'aprovechamiento_desc']
    
    # Encontrar la posición de esta optimización en la lista
    for idx, opt in enumerate(todas_optimizaciones, start=1):
        if opt.id == optimizacion.id:
            # Calcular número de lista según el ordenamiento
            if es_descendente:
                numero_lista = total_optimizaciones - idx + 1
            else:
                numero_lista = idx
            break
    else:
        numero_lista = None  # Si no se encuentra, usar ID por defecto
    
    # Regenerar las imágenes desde los datos guardados
    # Obtener unidad de la optimización
    unidad_opt = getattr(optimizacion, 'unidad_medida', 'cm') or 'cm'
    
    # Las piezas se guardaron en la unidad original, necesitamos convertirlas a cm
    piezas = []
    nombres_piezas = []
    for linea in optimizacion.piezas.splitlines():
        partes = linea.split(",")
        if len(partes) == 4:  # Con nombre
            nombre, w, h, c = partes
            nombres_piezas.append(nombre.strip())
            # Convertir de unidad original a cm
            w_cm = convertir_a_cm(float(w), unidad_opt)
            h_cm = convertir_a_cm(float(h), unidad_opt)
            piezas.append((w_cm, h_cm, int(c)))
        else:  # Sin nombre (formato antiguo)
            w, h, c = partes
            nombres_piezas.append(f"Pieza {len(nombres_piezas)+1}")
            # Convertir de unidad original a cm
            w_cm = convertir_a_cm(float(w), unidad_opt)
            h_cm = convertir_a_cm(float(h), unidad_opt)
            piezas.append((w_cm, h_cm, int(c)))
    
    # Generar TODAS las imágenes nuevamente (con info de desperdicio)
    # Nota: ancho_tablero y alto_tablero ya están en cm en la BD
    # Usar los parámetros de rotación y margen de corte guardados
    permitir_rotacion = getattr(optimizacion, 'permitir_rotacion', True)
    margen_corte = getattr(optimizacion, 'margen_corte', 0.3)
    
    imagenes_base64, _, info_desperdicio = generar_grafico(
        piezas, optimizacion.ancho_tablero, optimizacion.alto_tablero, unidad_opt,
        permitir_rotacion=permitir_rotacion,
        margen_corte=margen_corte,
        nombres_piezas=nombres_piezas
    )
    
    # Generar UN SOLO PDF con todas las imágenes (usando número de lista)
    pdf_path = generar_pdf(optimizacion, imagenes_base64, numero_lista=numero_lista)
    
    full_path = os.path.join(settings.MEDIA_ROOT, pdf_path)
    return FileResponse(open(full_path, "rb"), as_attachment=True, filename=os.path.basename(full_path))


@login_required
def descargar_excel(request, pk):
    """
    Descarga un archivo Excel con la información detallada de la optimización.
    """
    optimizacion = get_object_or_404(Optimizacion, pk=pk, usuario=request.user)
    
    # Obtener el ordenamiento actual desde los parámetros GET (si existe)
    ordenar_por = request.GET.get('ordenar_por', 'fecha_desc')
    
    # Aplicar el mismo ordenamiento que se usa en historial
    todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user)
    
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
    numero_lista = None
    for idx, opt in enumerate(todas_optimizaciones, start=1):
        if opt.id == optimizacion.id:
            if es_descendente:
                numero_lista = total_optimizaciones - idx + 1
            else:
                numero_lista = idx
            break
    
    # Regenerar las imágenes para obtener info_desperdicio
    unidad_opt = getattr(optimizacion, 'unidad_medida', 'cm') or 'cm'
    piezas = []
    piezas_con_nombre = []
    
    for linea in optimizacion.piezas.splitlines():
        if linea.strip():
            partes = linea.split(',')
            if len(partes) == 4:
                nombre, w, h, c = partes
                w_cm = convertir_a_cm(float(w), unidad_opt)
                h_cm = convertir_a_cm(float(h), unidad_opt)
                piezas.append((w_cm, h_cm, int(c)))
                piezas_con_nombre.append({
                    'nombre': nombre.strip(),
                    'ancho': float(w),
                    'alto': float(h),
                    'cantidad': int(c)
                })
            elif len(partes) == 3:
                w, h, c = partes
                w_cm = convertir_a_cm(float(w), unidad_opt)
                h_cm = convertir_a_cm(float(h), unidad_opt)
                piezas.append((w_cm, h_cm, int(c)))
                piezas_con_nombre.append({
                    'nombre': 'Pieza',
                    'ancho': float(w),
                    'alto': float(h),
                    'cantidad': int(c)
                })
    
    # Regenerar gráfico para obtener info_desperdicio
    permitir_rotacion = getattr(optimizacion, 'permitir_rotacion', True)
    margen_corte = getattr(optimizacion, 'margen_corte', 0.3)
    nombres_piezas = [p['nombre'] for p in piezas_con_nombre]
    
    _, _, info_desperdicio = generar_grafico(
        piezas, optimizacion.ancho_tablero, optimizacion.alto_tablero, unidad_opt,
        permitir_rotacion=permitir_rotacion,
        margen_corte=margen_corte,
        nombres_piezas=nombres_piezas
    )
    
    # Convertir áreas a la unidad del usuario
    factor_lineal = convertir_desde_cm(1, unidad_opt)
    factor_area = factor_lineal ** 2
    
    info_desperdicio_convertida = {
        'area_usada_total': round(info_desperdicio['area_usada_total'] * factor_area, 2),
        'desperdicio_total': round(info_desperdicio['desperdicio_total'] * factor_area, 2),
        'info_tableros': [
            {
                **info,
                'area_usada': round(info['area_usada'] * factor_area, 2),
                'desperdicio': round(info['desperdicio'] * factor_area, 2),
            }
            for info in info_desperdicio['info_tableros']
        ]
    }
    
    # Generar Excel
    excel_buffer = generar_excel(optimizacion, info_desperdicio_convertida, piezas_con_nombre, numero_lista)
    
    # Preparar respuesta
    from django.http import HttpResponse
    response = HttpResponse(
        excel_buffer.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="optimizacion_{numero_lista if numero_lista else optimizacion.id}.xlsx"'
    
    return response


@login_required
def resultado_view(request, pk=None):
    """
    Vista para mostrar el resultado de una optimización.
    Si pk está presente, muestra una optimización existente.
    Si es POST, procesa una nueva optimización.
    """
    # Si hay un pk, mostrar optimización existente
    if pk:
        optimizacion = get_object_or_404(Optimizacion, pk=pk, usuario=request.user)
        
        # Recuperar datos de la optimización guardada
        unidad = getattr(optimizacion, 'unidad_medida', 'cm') or 'cm'
        
        # Parsear piezas
        piezas_con_nombre = []
        for linea in optimizacion.piezas.splitlines():
            if linea.strip():
                partes = linea.split(',')
                if len(partes) == 4:
                    piezas_con_nombre.append({
                        'nombre': partes[0].strip(),
                        'ancho': float(partes[1].strip()),
                        'alto': float(partes[2].strip()),
                        'cantidad': int(partes[3].strip())
                    })
        
        # Regenerar la optimización para obtener todas las imágenes y detalles
        # Parsear piezas para regenerar - formato: (ancho, alto, cantidad)
        piezas_para_optimizar = []
        nombres_piezas = []
        for pieza in piezas_con_nombre:
            ancho_val = pieza['ancho']
            alto_val = pieza['alto']
            cantidad = pieza['cantidad']
            nombre = pieza['nombre']
            
            # Convertir a cm si es necesario
            ancho_cm = convertir_a_cm(ancho_val, unidad)
            alto_cm = convertir_a_cm(alto_val, unidad)
            
            # Agregar como tupla de 3 elementos (ancho, alto, cantidad)
            piezas_para_optimizar.append((ancho_cm, alto_cm, cantidad))
            nombres_piezas.append(nombre)
        
        # Obtener parámetros de la optimización
        margen_corte = getattr(optimizacion, 'margen_corte', 0.3) or 0.3
        permitir_rotacion = getattr(optimizacion, 'permitir_rotacion', True)
        
        # Regenerar gráfico y obtener información completa
        # generar_grafico retorna: (imagenes_base64, aprovechamiento_total, info_desperdicio_dict)
        imagenes_base64, aprovechamiento, info_desperdicio = generar_grafico(
            piezas_para_optimizar,
            optimizacion.ancho_tablero,
            optimizacion.alto_tablero,
            unidad='cm',
            permitir_rotacion=permitir_rotacion,
            margen_corte=margen_corte,
            nombres_piezas=nombres_piezas if nombres_piezas else None
        )
        
        imagen_principal = imagenes_base64[0] if imagenes_base64 else None
        num_tableros = len(imagenes_base64)
        
        # Convertir áreas a la unidad del usuario
        simbolo_area = obtener_simbolo_area(unidad)
        factor_lineal = convertir_desde_cm(1, unidad)
        factor_area = factor_lineal ** 2
        
        area_usada_mostrar = round(info_desperdicio['area_usada_total'] * factor_area, 2)
        desperdicio_mostrar = round(info_desperdicio['desperdicio_total'] * factor_area, 2)
        
        # Convertir info de tableros
        info_tableros_convertida = []
        for info in info_desperdicio['info_tableros']:
            area_usada_tab = round(info['area_usada'] * factor_area, 2)
            desperdicio_tab = round(info['desperdicio'] * factor_area, 2)
            info_tableros_convertida.append({
                **info,
                'area_usada': area_usada_tab,
                'desperdicio': desperdicio_tab,
            })
        
        info_desperdicio_mostrar = {
            **info_desperdicio,
            'area_usada_total': area_usada_mostrar,
            'desperdicio_total': desperdicio_mostrar,
            'info_tableros': info_tableros_convertida,
        }
        
        # Combinar imágenes con información de tableros
        tableros_con_imagenes = []
        for idx, (img, info) in enumerate(zip(imagenes_base64, info_tableros_convertida), start=1):
            tableros_con_imagenes.append({
                'numero': info['numero'],
                'imagen': img,
                'info': info
            })
        
        # Calcular costos
        costo_total = optimizacion.get_costo_total()
        costo_material = None
        precio_tablero = optimizacion.precio_tablero
        mano_obra = optimizacion.mano_obra or Decimal('0.00')
        
        if precio_tablero:
            costo_material = Decimal(str(num_tableros)) * precio_tablero
        
        # Calcular número de lista para el PDF (basado en orden por fecha descendente)
        todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user).order_by('-fecha')
        total_optimizaciones = todas_optimizaciones.count()
        
        numero_lista = optimizacion.pk
        for idx, opt in enumerate(todas_optimizaciones, start=1):
            if opt.id == optimizacion.id:
                numero_lista = total_optimizaciones - idx + 1
                break
        
        # Generar PDF si es necesario
        pdf_path = None
        try:
            pdf_path = generar_pdf(optimizacion, imagenes_base64, numero_lista=numero_lista)
        except Exception as e:
            pass  # No es crítico si falla el PDF
        
        return render(request, "opticut/resultado.html", {
            "optimizacion": optimizacion,
            "imagen": imagen_principal,
            "imagenes": imagenes_base64,
            "pdf_path": pdf_path,
            "num_tableros": num_tableros,
            "piezas_con_nombre": piezas_con_nombre,
            "info_desperdicio": info_desperdicio_mostrar,
            "tableros_con_imagenes": tableros_con_imagenes,
            "numero_lista": numero_lista,
            "unidad_medida": unidad,
            "simbolo_area": simbolo_area,
            "costo_total": costo_total,
            "costo_material": costo_material,
            "precio_tablero": precio_tablero,
            "mano_obra": mano_obra,
        })
    
    if request.method == "POST":
        ancho = float(request.POST.get("ancho_tablero"))
        alto = float(request.POST.get("alto_tablero"))
        piezas_texto = request.POST.get("piezas")

        piezas = []
        piezas_con_nombre = []
        for linea in piezas_texto.strip().splitlines():
            partes = linea.split(",")
            if len(partes) == 4:  # Con nombre
                nombre, w, h, c = partes
                piezas.append((float(w), float(h), int(c)))
                piezas_con_nombre.append({
                    'nombre': nombre.strip(),
                    'ancho': float(w),
                    'alto': float(h),
                    'cantidad': int(c)
                })
            else:  # Sin nombre
                w, h, c = partes
                piezas.append((float(w), float(h), int(c)))
                piezas_con_nombre.append({
                    'nombre': 'Pieza',
                    'ancho': float(w),
                    'alto': float(h),
                    'cantidad': int(c)
                })

        # Obtener unidad (asumir cm para datos antiguos o del POST)
        unidad_resultado = request.POST.get('unidad_medida', 'cm')
        if not unidad_resultado:
            unidad_resultado = 'cm'
        
        # Obtener parámetros de rotación y margen de corte (valores por defecto para compatibilidad)
        permitir_rotacion = request.POST.get('permitir_rotacion', 'true').lower() == 'true'
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
        
        # Generar TODAS las imágenes con info de desperdicio
        imagenes_base64, aprovechamiento, info_desperdicio = generar_grafico(
            piezas, ancho, alto, unidad_resultado,
            permitir_rotacion=permitir_rotacion,
            margen_corte=margen_corte_cm,
            nombres_piezas=nombres_piezas
        )
        imagen_principal = imagenes_base64[0] if imagenes_base64 else ""
        
        num_tableros = len(imagenes_base64)

        optimizacion = Optimizacion.objects.create(
            usuario=request.user,
            ancho_tablero=ancho,
            alto_tablero=alto,
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

        # Guardar la primera imagen en el modelo
        if imagen_principal:
            image_data = base64.b64decode(imagen_principal)
            file = ContentFile(image_data)
            optimizacion.imagen.save(f"optimizacion_{request.user.username}_{optimizacion.id}.png", file)

        # Calcular el número de lista para el PDF (basado en orden por fecha descendente por defecto)
        todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user).order_by('-fecha')
        total_optimizaciones = todas_optimizaciones.count()
        
        # Encontrar la posición real de esta optimización en la lista ordenada
        for idx, opt in enumerate(todas_optimizaciones, start=1):
            if opt.id == optimizacion.id:
                numero_lista = total_optimizaciones - idx + 1
                break
        else:
            numero_lista = total_optimizaciones

        # Generar UN SOLO PDF con todas las imágenes usando el número de lista correcto
        pdf_path = generar_pdf(optimizacion, imagenes_base64, numero_lista=numero_lista)
        optimizacion.pdf = pdf_path
        optimizacion.save()
        
        # Enviar notificación de optimización completada
        enviar_notificacion(
            request,
            'optimizacion_completada',
            'Optimización Completada',
            f'Tu optimización #{numero_lista} ha sido completada exitosamente con un aprovechamiento del {aprovechamiento:.2f}%.',
            {'optimizacion_id': optimizacion.id, 'aprovechamiento': aprovechamiento}
        )

        # Obtener unidad de la optimización
        unidad = getattr(optimizacion, 'unidad_medida', 'cm') or 'cm'
        
        # Convertir áreas de cm² a la unidad del usuario para mostrar
        simbolo_area = obtener_simbolo_area(unidad)
        factor_lineal = convertir_desde_cm(1, unidad)
        factor_area = factor_lineal ** 2
        
        area_usada_mostrar = round(info_desperdicio['area_usada_total'] * factor_area, 2)
        desperdicio_mostrar = round(info_desperdicio['desperdicio_total'] * factor_area, 2)
        
        info_tableros_convertida = []
        for info in info_desperdicio['info_tableros']:
            area_usada_tab = round(info['area_usada'] * factor_area, 2)
            desperdicio_tab = round(info['desperdicio'] * factor_area, 2)
            info_tableros_convertida.append({
                **info,
                'area_usada': area_usada_tab,
                'desperdicio': desperdicio_tab,
            })
        
        info_desperdicio_mostrar = {
            **info_desperdicio,
            'area_usada_total': area_usada_mostrar,
            'desperdicio_total': desperdicio_mostrar,
            'info_tableros': info_tableros_convertida,
        }
        
        # Combinar imágenes con información de tableros para asegurar enumeración correcta
        tableros_con_imagenes = []
        for idx, (img, info) in enumerate(zip(imagenes_base64, info_tableros_convertida), start=1):
            tableros_con_imagenes.append({
                'numero': info['numero'],
                'imagen': img,
                'info': info
            })
        
        # Calcular costos
        costo_total = optimizacion.get_costo_total()
        costo_material = None
        if precio_tablero:
            costo_material = Decimal(str(num_tableros)) * precio_tablero
        
        return render(request, "opticut/resultado.html", {
            "optimizacion": optimizacion,
            "imagen": imagen_principal,
            "imagenes": imagenes_base64,
            "pdf_path": pdf_path,
            "num_tableros": len(imagenes_base64),
            "piezas_con_nombre": piezas_con_nombre,
            "info_desperdicio": info_desperdicio_mostrar,
            "tableros_con_imagenes": tableros_con_imagenes,
            "numero_lista": numero_lista,  # Pasar número de lista para usar en descarga PNG
            "unidad_medida": unidad,
            "simbolo_area": simbolo_area,
            "costo_total": costo_total,
            "costo_material": costo_material,
            "precio_tablero": precio_tablero,
            "mano_obra": mano_obra,
        })


@login_required
def imprimir_plan_corte(request, pk):
    """
    Vista para imprimir el plan de corte de una optimización.
    Renderiza un template optimizado para impresión.
    """
    optimizacion = get_object_or_404(Optimizacion, pk=pk, usuario=request.user)
    
    # Recuperar datos de la optimización guardada
    unidad = getattr(optimizacion, 'unidad_medida', 'cm') or 'cm'
    
    # Parsear piezas
    piezas_con_nombre = []
    for linea in optimizacion.piezas.splitlines():
        if linea.strip():
            partes = linea.split(',')
            if len(partes) == 4:
                ancho = float(partes[1].strip())
                alto = float(partes[2].strip())
                cantidad = int(partes[3].strip())
                area_unitaria = ancho * alto
                area_total = area_unitaria * cantidad
                piezas_con_nombre.append({
                    'nombre': partes[0].strip(),
                    'ancho': ancho,
                    'alto': alto,
                    'cantidad': cantidad,
                    'area_unitaria': area_unitaria,
                    'area_total': area_total
                })
    
    # Regenerar la optimización para obtener todas las imágenes y detalles
    piezas_para_optimizar = []
    nombres_piezas = []
    for pieza in piezas_con_nombre:
        ancho_val = pieza['ancho']
        alto_val = pieza['alto']
        cantidad = pieza['cantidad']
        nombre = pieza['nombre']
        
        # Convertir a cm si es necesario
        ancho_cm = convertir_a_cm(ancho_val, unidad)
        alto_cm = convertir_a_cm(alto_val, unidad)
        
        # Agregar como tupla de 3 elementos (ancho, alto, cantidad)
        piezas_para_optimizar.append((ancho_cm, alto_cm, cantidad))
        nombres_piezas.append(nombre)
    
    # Obtener parámetros de la optimización
    margen_corte = getattr(optimizacion, 'margen_corte', 0.3) or 0.3
    permitir_rotacion = getattr(optimizacion, 'permitir_rotacion', True)
    
    # Regenerar gráfico en modo plan de corte (blanco y negro, solo medidas)
    imagenes_base64, aprovechamiento, info_desperdicio = generar_grafico(
        piezas_para_optimizar,
        optimizacion.ancho_tablero,
        optimizacion.alto_tablero,
        unidad='cm',
        permitir_rotacion=permitir_rotacion,
        margen_corte=margen_corte,
        nombres_piezas=nombres_piezas if nombres_piezas else None,
        modo_plan_corte=True  # Modo blanco y negro para plan de corte
    )
    
    num_tableros = len(imagenes_base64)
    
    # Convertir áreas a la unidad del usuario
    simbolo_area = obtener_simbolo_area(unidad)
    simbolo_unidad = obtener_simbolo_unidad(unidad)
    factor_lineal = convertir_desde_cm(1, unidad)
    factor_area = factor_lineal ** 2
    
    area_usada_mostrar = round(info_desperdicio['area_usada_total'] * factor_area, 2)
    desperdicio_mostrar = round(info_desperdicio['desperdicio_total'] * factor_area, 2)
    
    # Convertir info de tableros
    info_tableros_convertida = []
    for info in info_desperdicio['info_tableros']:
        area_usada_tab = round(info['area_usada'] * factor_area, 2)
        desperdicio_tab = round(info['desperdicio'] * factor_area, 2)
        info_tableros_convertida.append({
            **info,
            'area_usada': area_usada_tab,
            'desperdicio': desperdicio_tab,
        })
    
    info_desperdicio_mostrar = {
        **info_desperdicio,
        'area_usada_total': area_usada_mostrar,
        'desperdicio_total': desperdicio_mostrar,
        'info_tableros': info_tableros_convertida,
    }
    
    # Combinar imágenes con información de tableros
    tableros_con_imagenes = []
    for idx, (img, info) in enumerate(zip(imagenes_base64, info_tableros_convertida), start=1):
        tableros_con_imagenes.append({
            'numero': info['numero'],
            'imagen': img,
            'info': info
        })
    
    # Calcular costos
    costo_total = optimizacion.get_costo_total()
    costo_material = None
    precio_tablero = optimizacion.precio_tablero
    mano_obra = optimizacion.mano_obra or Decimal('0.00')
    
    if precio_tablero:
        costo_material = Decimal(str(num_tableros)) * precio_tablero
    
    # Calcular número de lista
    todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user).order_by('-fecha')
    total_optimizaciones = todas_optimizaciones.count()
    
    numero_lista = optimizacion.pk
    for idx, opt in enumerate(todas_optimizaciones, start=1):
        if opt.id == optimizacion.id:
            numero_lista = total_optimizaciones - idx + 1
            break
    
    return render(request, "opticut/imprimir_plan_corte.html", {
        "optimizacion": optimizacion,
        "imagenes": imagenes_base64,
        "num_tableros": num_tableros,
        "piezas_con_nombre": piezas_con_nombre,
        "info_desperdicio": info_desperdicio_mostrar,
        "tableros_con_imagenes": tableros_con_imagenes,
        "numero_lista": numero_lista,
        "unidad_medida": unidad,
        "simbolo_area": simbolo_area,
        "simbolo_unidad": simbolo_unidad,
        "costo_total": costo_total,
        "costo_material": costo_material,
        "precio_tablero": precio_tablero,
        "mano_obra": mano_obra,
    })


@login_required
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
    
    return render(request, "opticut/index.html", {
        "tablero_form": tablero_form,
        "pieza_formset": pieza_formset,
        "duplicando": True,
        "optimizacion_original": optimizacion
    })


@login_required
def estadisticas(request):
    """
    Vista para mostrar estadísticas, gráficos y top de optimizaciones.
    
    IMPORTANTE: Todos los datos están filtrados por usuario (request.user).
    Cada usuario solo ve sus propias optimizaciones y estadísticas.
    """
    # Obtener todas las optimizaciones del usuario actual (filtrado por seguridad)
    todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user).order_by('fecha')
    
    # Obtener período seleccionado
    periodo = request.GET.get('periodo', 'todos')
    
    # Filtrar por período
    ahora = timezone.now()
    optimizaciones_filtradas = todas_optimizaciones
    
    if periodo == 'semanal':
        fecha_limite = ahora - timedelta(days=7)
        optimizaciones_filtradas = todas_optimizaciones.filter(fecha__gte=fecha_limite)
    elif periodo == 'mensual':
        fecha_limite = ahora - timedelta(days=30)
        optimizaciones_filtradas = todas_optimizaciones.filter(fecha__gte=fecha_limite)
    elif periodo == 'anual':
        fecha_limite = ahora - timedelta(days=365)
        optimizaciones_filtradas = todas_optimizaciones.filter(fecha__gte=fecha_limite)
    # 'todos' no necesita filtro
    
    # Calcular estadísticas generales
    total_optimizaciones = optimizaciones_filtradas.count()
    
    if total_optimizaciones > 0:
        # Estadísticas de aprovechamiento
        promedio_aprovechamiento = optimizaciones_filtradas.aggregate(
            avg=Avg('aprovechamiento_total')
        )['avg'] or 0
        
        max_aprovechamiento = optimizaciones_filtradas.order_by('-aprovechamiento_total').first()
        max_aprovech_val = max_aprovechamiento.aprovechamiento_total if max_aprovechamiento else 0
        
        min_aprovechamiento = optimizaciones_filtradas.order_by('aprovechamiento_total').first()
        min_aprovech_val = min_aprovechamiento.aprovechamiento_total if min_aprovechamiento else 0
        
        # Estadísticas de desperdicio (calculado)
        promedio_desperdicio = 100 - promedio_aprovechamiento
        
        # Top 10 optimizaciones (mayor aprovechamiento)
        top_optimizaciones = optimizaciones_filtradas.order_by('-aprovechamiento_total')[:10]
        
        # Generar gráficos (versión normal y alta resolución)
        grafico_aprovechamiento = generar_grafico_aprovechamiento(
            optimizaciones_filtradas.order_by('fecha'), periodo, alta_resolucion=False
        )
        grafico_aprovechamiento_hd = generar_grafico_aprovechamiento(
            optimizaciones_filtradas.order_by('fecha'), periodo, alta_resolucion=True
        )
        grafico_desperdicio = generar_grafico_desperdicio(
            optimizaciones_filtradas.order_by('fecha'), periodo, alta_resolucion=False
        )
        grafico_desperdicio_hd = generar_grafico_desperdicio(
            optimizaciones_filtradas.order_by('fecha'), periodo, alta_resolucion=True
        )
    else:
        promedio_aprovechamiento = 0
        max_aprovech_val = 0
        min_aprovech_val = 0
        promedio_desperdicio = 0
        top_optimizaciones = []
        grafico_aprovechamiento = None
        grafico_aprovechamiento_hd = None
        grafico_desperdicio = None
        grafico_desperdicio_hd = None
    
    # Procesar top optimizaciones para el template
    top_optimizaciones_list = []
    for idx, opt in enumerate(top_optimizaciones, start=1):
        # Parsear piezas
        piezas_procesadas = []
        for linea in opt.piezas.splitlines():
            if linea.strip():
                partes = linea.split(',')
                if len(partes) == 4:
                    piezas_procesadas.append({
                        'nombre': partes[0].strip(),
                        'ancho': partes[1].strip(),
                        'alto': partes[2].strip(),
                        'cantidad': partes[3].strip()
                    })
                elif len(partes) == 3:
                    piezas_procesadas.append({
                        'nombre': 'Pieza',
                        'ancho': partes[0].strip(),
                        'alto': partes[1].strip(),
                        'cantidad': partes[2].strip()
                    })
        
        # Obtener unidad y convertir dimensiones para mostrar
        unidad_opt = getattr(opt, 'unidad_medida', 'cm') or 'cm'
        ancho_mostrar = round(convertir_desde_cm(opt.ancho_tablero, unidad_opt), 2)
        alto_mostrar = round(convertir_desde_cm(opt.alto_tablero, unidad_opt), 2)
        
        top_optimizaciones_list.append({
            'optimizacion': opt,
            'posicion': idx,
            'piezas': piezas_procesadas,
            'ancho_mostrar': ancho_mostrar,
            'alto_mostrar': alto_mostrar,
            'unidad_medida': unidad_opt,
        })
    
    return render(request, 'opticut/estadisticas.html', {
        'total_optimizaciones': total_optimizaciones,
        'promedio_aprovechamiento': round(promedio_aprovechamiento, 2),
        'max_aprovechamiento': round(max_aprovech_val, 2),
        'min_aprovechamiento': round(min_aprovech_val, 2),
        'promedio_desperdicio': round(promedio_desperdicio, 2),
        'top_optimizaciones': top_optimizaciones_list,
        'grafico_aprovechamiento': grafico_aprovechamiento,
        'grafico_aprovechamiento_hd': grafico_aprovechamiento_hd,
        'grafico_desperdicio': grafico_desperdicio,
        'grafico_desperdicio_hd': grafico_desperdicio_hd,
        'periodo': periodo,
        'optimizaciones_filtradas': optimizaciones_filtradas,
    })


@login_required
def exportar_excel_desperdicio(request):
    """
    Exporta un Excel con el resumen de desperdicio desde estadísticas.
    """
    from django.http import HttpResponse
    from .utils import generar_excel_resumen_desperdicio
    
    try:
        # Obtener todas las optimizaciones del usuario
        todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user)
        
        # Obtener período seleccionado
        periodo = request.GET.get('periodo', 'todos')
        
        # Filtrar por período
        ahora = timezone.now()
        optimizaciones_filtradas = todas_optimizaciones
        
        if periodo == 'semanal':
            fecha_limite = ahora - timedelta(days=7)
            optimizaciones_filtradas = todas_optimizaciones.filter(fecha__gte=fecha_limite)
        elif periodo == 'mensual':
            fecha_limite = ahora - timedelta(days=30)
            optimizaciones_filtradas = todas_optimizaciones.filter(fecha__gte=fecha_limite)
        elif periodo == 'anual':
            fecha_limite = ahora - timedelta(days=365)
            optimizaciones_filtradas = todas_optimizaciones.filter(fecha__gte=fecha_limite)
        
        # Calcular estadísticas
        total_optimizaciones = optimizaciones_filtradas.count()
        
        if total_optimizaciones > 0:
            promedio_aprovechamiento = optimizaciones_filtradas.aggregate(
                avg=Avg('aprovechamiento_total')
            )['avg'] or 0
            max_aprovechamiento = optimizaciones_filtradas.order_by('-aprovechamiento_total').first()
            max_aprovech_val = max_aprovechamiento.aprovechamiento_total if max_aprovechamiento else 0
            min_aprovechamiento = optimizaciones_filtradas.order_by('aprovechamiento_total').first()
            min_aprovech_val = min_aprovechamiento.aprovechamiento_total if min_aprovechamiento else 0
            promedio_desperdicio = 100 - promedio_aprovechamiento
        else:
            promedio_aprovechamiento = 0
            max_aprovech_val = 0
            min_aprovech_val = 0
            promedio_desperdicio = 0
        
        estadisticas = {
            'total_optimizaciones': total_optimizaciones,
            'promedio_aprovechamiento': promedio_aprovechamiento,
            'max_aprovechamiento': max_aprovech_val,
            'min_aprovechamiento': min_aprovech_val,
            'promedio_desperdicio': promedio_desperdicio,
        }
        
        # Generar Excel
        buffer = generar_excel_resumen_desperdicio(optimizaciones_filtradas, estadisticas, periodo)
        
        # Preparar respuesta
        periodo_nombre = {
            'todos': 'todos',
            'semanal': 'semanal',
            'mensual': 'mensual',
            'anual': 'anual'
        }.get(periodo, 'todos')
        
        filename = f"resumen_desperdicio_{periodo_nombre}_{timezone.now().strftime('%Y%m%d')}.xlsx"
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        messages.error(request, f"Error generando Excel: {e}")
        return redirect('opticut:estadisticas')


@login_required
def exportar_pdf_desperdicio(request):
    """
    Exporta un PDF con el resumen de desperdicio desde estadísticas.
    """
    from django.http import FileResponse
    from .utils import generar_pdf_resumen_desperdicio
    
    try:
        # Obtener todas las optimizaciones del usuario
        todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user)
        
        # Obtener período seleccionado
        periodo = request.GET.get('periodo', 'todos')
        
        # Filtrar por período
        ahora = timezone.now()
        optimizaciones_filtradas = todas_optimizaciones
        
        if periodo == 'semanal':
            fecha_limite = ahora - timedelta(days=7)
            optimizaciones_filtradas = todas_optimizaciones.filter(fecha__gte=fecha_limite)
        elif periodo == 'mensual':
            fecha_limite = ahora - timedelta(days=30)
            optimizaciones_filtradas = todas_optimizaciones.filter(fecha__gte=fecha_limite)
        elif periodo == 'anual':
            fecha_limite = ahora - timedelta(days=365)
            optimizaciones_filtradas = todas_optimizaciones.filter(fecha__gte=fecha_limite)
        
        # Calcular estadísticas
        total_optimizaciones = optimizaciones_filtradas.count()
        
        if total_optimizaciones > 0:
            promedio_aprovechamiento = optimizaciones_filtradas.aggregate(
                avg=Avg('aprovechamiento_total')
            )['avg'] or 0
            max_aprovechamiento = optimizaciones_filtradas.order_by('-aprovechamiento_total').first()
            max_aprovech_val = max_aprovechamiento.aprovechamiento_total if max_aprovechamiento else 0
            min_aprovechamiento = optimizaciones_filtradas.order_by('aprovechamiento_total').first()
            min_aprovech_val = min_aprovechamiento.aprovechamiento_total if min_aprovechamiento else 0
            promedio_desperdicio = 100 - promedio_aprovechamiento
        else:
            promedio_aprovechamiento = 0
            max_aprovech_val = 0
            min_aprovech_val = 0
            promedio_desperdicio = 0
        
        estadisticas = {
            'total_optimizaciones': total_optimizaciones,
            'promedio_aprovechamiento': promedio_aprovechamiento,
            'max_aprovechamiento': max_aprovech_val,
            'min_aprovechamiento': min_aprovech_val,
            'promedio_desperdicio': promedio_desperdicio,
        }
        
        # Generar PDF
        pdf_path = generar_pdf_resumen_desperdicio(optimizaciones_filtradas, estadisticas, periodo)
        
        # pdf_path ya es relativo (pdfs/filename.pdf)
        full_path = os.path.join(settings.MEDIA_ROOT, pdf_path)
        filename = os.path.basename(pdf_path)
        return FileResponse(open(full_path, "rb"), as_attachment=True, filename=filename)
        
    except Exception as e:
        messages.error(request, f"Error generando PDF: {e}")
        return redirect('opticut:estadisticas')


@login_required
def toggle_favorito(request, pk):
    """
    Marca o desmarca una optimización como favorita.
    Soporta tanto peticiones AJAX como peticiones normales.
    """
    optimizacion = get_object_or_404(Optimizacion, pk=pk, usuario=request.user)
    optimizacion.favorito = not optimizacion.favorito
    optimizacion.save()
    
    # Si es una petición AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax') == 'true':
        from django.http import JsonResponse
        return JsonResponse({
            'success': True,
            'favorito': optimizacion.favorito,
            'message': f"⭐ Optimización #{pk} marcada como favorita." if optimizacion.favorito else f"Optimización #{pk} eliminada de favoritos."
        })
    
    # Si no es AJAX, comportamiento normal con mensajes
    if optimizacion.favorito:
        messages.success(request, f"⭐ Optimización #{pk} marcada como favorita.")
    else:
        messages.info(request, f"Optimización #{pk} eliminada de favoritos.")
    
    # Redirigir de vuelta a historial, manteniendo los filtros (solo si no es AJAX)
    return redirect(request.META.get('HTTP_REFERER', 'opticut:historial'))


@login_required
def calcular_tiempo_corte(request, pk):
    """
    Calcula el tiempo estimado de corte para una optimización.
    Considera: número de piezas, tipo de corte, material, etc.
    """
    optimizacion = get_object_or_404(Optimizacion, pk=pk, usuario=request.user)
    
    # Obtener parámetros de cálculo (pueden venir del POST o usar valores por defecto)
    velocidad_corte = float(request.POST.get('velocidad_corte', 2.0))  # cm/segundo (por defecto)
    tiempo_setup = float(request.POST.get('tiempo_setup', 5.0))  # minutos por tablero
    tiempo_cambio_herramienta = float(request.POST.get('tiempo_cambio_herramienta', 2.0))  # minutos
    
    # Parsear piezas
    piezas = []
    total_piezas = 0
    perimetro_total = 0  # Perímetro total a cortar en cm
    
    for linea in optimizacion.piezas.splitlines():
        if linea.strip():
            partes = linea.split(',')
            if len(partes) == 4:
                nombre, ancho, alto, cantidad = partes
                ancho_cm = convertir_a_cm(float(ancho), optimizacion.unidad_medida)
                alto_cm = convertir_a_cm(float(alto), optimizacion.unidad_medida)
            elif len(partes) == 3:
                ancho, alto, cantidad = partes
                ancho_cm = convertir_a_cm(float(ancho), optimizacion.unidad_medida)
                alto_cm = convertir_a_cm(float(alto), optimizacion.unidad_medida)
            
            cantidad = int(cantidad)
            total_piezas += cantidad
            # Perímetro de cada pieza: 2*(ancho + alto)
            perimetro_pieza = 2 * (ancho_cm + alto_cm)
            perimetro_total += perimetro_pieza * cantidad
    
    # Calcular número de tableros (aproximado basado en el área)
    area_tablero = optimizacion.ancho_tablero * optimizacion.alto_tablero
    area_total_piezas = sum(
        convertir_a_cm(float(p.split(',')[1]), optimizacion.unidad_medida) * 
        convertir_a_cm(float(p.split(',')[2]), optimizacion.unidad_medida) * 
        int(p.split(',')[3]) 
        for p in optimizacion.piezas.splitlines() if p.strip()
    )
    num_tableros_estimado = max(1, int(area_total_piezas / area_tablero) + 1)
    
    # Calcular tiempos
    # Tiempo de corte = perímetro total / velocidad de corte
    tiempo_corte_segundos = perimetro_total / velocidad_corte
    tiempo_corte_minutos = tiempo_corte_segundos / 60
    
    # Tiempo de setup (preparación de cada tablero)
    tiempo_setup_total = tiempo_setup * num_tableros_estimado
    
    # Tiempo de cambio de herramienta (estimado: 1 cambio por cada 10 piezas diferentes)
    tipos_piezas = len([p for p in optimizacion.piezas.splitlines() if p.strip()])
    cambios_herramienta = max(0, tipos_piezas - 1)
    tiempo_cambio_total = tiempo_cambio_herramienta * cambios_herramienta
    
    # Tiempo total estimado
    tiempo_total_minutos = tiempo_corte_minutos + tiempo_setup_total + tiempo_cambio_total
    tiempo_total_horas = tiempo_total_minutos / 60
    
    # Formatear tiempo
    horas = int(tiempo_total_horas)
    minutos = int(tiempo_total_minutos % 60)
    segundos = int((tiempo_total_minutos % 1) * 60)
    
    # Calcular porcentajes
    porcentaje_corte = round((tiempo_corte_minutos / tiempo_total_minutos * 100) if tiempo_total_minutos > 0 else 0, 1)
    porcentaje_setup = round((tiempo_setup_total / tiempo_total_minutos * 100) if tiempo_total_minutos > 0 else 0, 1)
    porcentaje_cambio = round((tiempo_cambio_total / tiempo_total_minutos * 100) if tiempo_total_minutos > 0 else 0, 1)
    
    # Preparar datos para mostrar
    unidad_opt = getattr(optimizacion, 'unidad_medida', 'cm') or 'cm'
    ancho_mostrar = round(convertir_desde_cm(optimizacion.ancho_tablero, unidad_opt), 2)
    alto_mostrar = round(convertir_desde_cm(optimizacion.alto_tablero, unidad_opt), 2)
    
    return render(request, 'opticut/calcular_tiempo.html', {
        'optimizacion': optimizacion,
        'ancho_mostrar': ancho_mostrar,
        'alto_mostrar': alto_mostrar,
        'unidad_medida': unidad_opt,
        'total_piezas': total_piezas,
        'tipos_piezas': tipos_piezas,
        'num_tableros_estimado': num_tableros_estimado,
        'perimetro_total': round(perimetro_total, 2),
        'tiempo_corte_minutos': round(tiempo_corte_minutos, 2),
        'tiempo_setup_total': round(tiempo_setup_total, 2),
        'tiempo_cambio_total': round(tiempo_cambio_total, 2),
        'tiempo_total_minutos': round(tiempo_total_minutos, 2),
        'tiempo_total_horas': round(tiempo_total_horas, 2),
        'tiempo_formateado': f"{horas}h {minutos}m {segundos}s" if horas > 0 else f"{minutos}m {segundos}s",
        'velocidad_corte': velocidad_corte,
        'tiempo_setup': tiempo_setup,
        'tiempo_cambio_herramienta': tiempo_cambio_herramienta,
        'porcentaje_corte': porcentaje_corte,
        'porcentaje_setup': porcentaje_setup,
        'porcentaje_cambio': porcentaje_cambio,
        'velocidad_corte_cm_min': round(velocidad_corte * 60, 0),
    })


@login_required
def descargar_png(request, pk, tablero_num=None):
    """
    Descarga una imagen PNG de un tablero específico de una optimización.
    Si tablero_num no se especifica, descarga la primera imagen (tablero 1).
    """
    optimizacion = get_object_or_404(Optimizacion, pk=pk, usuario=request.user)
    
    # Obtener el ordenamiento actual desde los parámetros GET (si existe)
    ordenar_por = request.GET.get('ordenar_por', 'fecha_desc')
    
    # Aplicar el mismo ordenamiento que se usa en historial
    todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user)
    
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
    
    # Determinar si el ordenamiento es descendente o ascendente
    es_descendente = ordenar_por in ['fecha_desc', 'aprovechamiento_desc']
    
    # Encontrar la posición de esta optimización en la lista
    numero_lista = None
    for idx, opt in enumerate(todas_optimizaciones, start=1):
        if opt.id == optimizacion.id:
            # Calcular número de lista según el ordenamiento
            if es_descendente:
                numero_lista = total_optimizaciones - idx + 1
            else:
                numero_lista = idx
            break
    
    # Obtener unidad de la optimización
    unidad_opt = getattr(optimizacion, 'unidad_medida', 'cm') or 'cm'
    
    # Parsear piezas y convertir a cm
    piezas = []
    nombres_piezas = []
    for linea in optimizacion.piezas.splitlines():
        if linea.strip():
            partes = linea.split(",")
            if len(partes) == 4:  # Con nombre
                nombre, w, h, c = partes
                nombres_piezas.append(nombre.strip())
                w_cm = convertir_a_cm(float(w), unidad_opt)
                h_cm = convertir_a_cm(float(h), unidad_opt)
                piezas.append((w_cm, h_cm, int(c)))
            elif len(partes) == 3:  # Sin nombre
                w, h, c = partes
                nombres_piezas.append(f"Pieza {len(nombres_piezas)+1}")
                w_cm = convertir_a_cm(float(w), unidad_opt)
                h_cm = convertir_a_cm(float(h), unidad_opt)
                piezas.append((w_cm, h_cm, int(c)))
    
    # Generar todas las imágenes (usando parámetros guardados)
    permitir_rotacion = getattr(optimizacion, 'permitir_rotacion', True)
    margen_corte = getattr(optimizacion, 'margen_corte', 0.3)
    
    imagenes_base64, _, _ = generar_grafico(
        piezas, optimizacion.ancho_tablero, optimizacion.alto_tablero, unidad_opt,
        permitir_rotacion=permitir_rotacion,
        margen_corte=margen_corte,
        nombres_piezas=nombres_piezas
    )
    
    if not imagenes_base64:
        messages.error(request, "No se encontraron imágenes para esta optimización.")
        return redirect('opticut:historial')
    
    # Determinar qué tablero descargar
    if tablero_num is None:
        tablero_num = 1
    
    # Validar que el número de tablero existe
    if tablero_num < 1 or tablero_num > len(imagenes_base64):
        messages.error(request, f"El tablero #{tablero_num} no existe. Esta optimización tiene {len(imagenes_base64)} tablero(s).")
        return redirect('opticut:historial')
    
    # Obtener la imagen del tablero solicitado (índice 0-based)
    imagen_base64 = imagenes_base64[tablero_num - 1]
    
    # Decodificar la imagen
    image_data = base64.b64decode(imagen_base64)
    
    # Crear respuesta HTTP con la imagen
    from django.http import HttpResponse
    response = HttpResponse(image_data, content_type='image/png')
    
    # Usar número de lista si está disponible (igual que en PDFs), sino usar el ID
    if numero_lista is not None:
        filename = f"tablero_{tablero_num}_optimizacion_{optimizacion.usuario.username}_{numero_lista}.png"
    else:
        filename = f"tablero_{tablero_num}_optimizacion_{optimizacion.usuario.username}_{optimizacion.id}.png"
    
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@login_required
def api_tableros_optimizacion(request, pk):
    """
    API que retorna todas las imágenes de tableros de una optimización en base64.
    """
    from django.http import JsonResponse
    
    optimizacion = get_object_or_404(Optimizacion, pk=pk, usuario=request.user)
    
    # Parsear piezas
    piezas = []
    nombres_piezas = []
    for linea in optimizacion.piezas.splitlines():
        partes = linea.split(',')
        if len(partes) >= 3:
            try:
                if len(partes) == 4:
                    nombres_piezas.append(partes[0].strip())
                    ancho = float(partes[1].strip())
                    alto = float(partes[2].strip())
                    cantidad = int(partes[3].strip())
                else:
                    nombres_piezas.append(f"Pieza {len(nombres_piezas)+1}")
                    ancho = float(partes[0].strip())
                    alto = float(partes[1].strip())
                    cantidad = int(partes[2].strip())
                
                ancho_cm = convertir_a_cm(ancho, optimizacion.unidad_medida)
                alto_cm = convertir_a_cm(alto, optimizacion.unidad_medida)
                piezas.append((ancho_cm, alto_cm, cantidad))
            except (ValueError, IndexError):
                continue
    
    # Generar todas las imágenes
    imagenes_base64, _, _ = generar_grafico(
        piezas,
        optimizacion.ancho_tablero,
        optimizacion.alto_tablero,
        unidad=optimizacion.unidad_medida,
        permitir_rotacion=getattr(optimizacion, 'permitir_rotacion', True),
        margen_corte=getattr(optimizacion, 'margen_corte', 0.3),
        nombres_piezas=nombres_piezas
    )
    
    return JsonResponse({
        'success': True,
        'imagenes': imagenes_base64,
        'total': len(imagenes_base64)
    })


# ===== VISTAS DE GESTIÓN DE MATERIALES =====

@login_required
def lista_materiales(request):
    """
    Lista todos los materiales del usuario y los predefinidos del sistema.
    """
    # Materiales del usuario
    materiales_usuario = Material.objects.filter(usuario=request.user)
    
    # Materiales predefinidos del sistema
    materiales_sistema = Material.objects.filter(es_predefinido=True)
    
    # Búsqueda
    busqueda = request.GET.get('busqueda', '').strip()
    if busqueda:
        materiales_usuario = materiales_usuario.filter(nombre__icontains=busqueda)
        materiales_sistema = materiales_sistema.filter(nombre__icontains=busqueda)
    
    return render(request, 'opticut/lista_materiales.html', {
        'materiales_usuario': materiales_usuario,
        'materiales_sistema': materiales_sistema,
        'busqueda': busqueda,
    })


@login_required
def crear_material(request):
    """
    Crea un nuevo material.
    """
    if request.method == "POST":
        form = MaterialForm(request.POST)
        if form.is_valid():
            material = form.save(commit=False)
            material.usuario = request.user
            material.es_predefinido = False  # Solo admin puede crear predefinidos
            material.save()
            messages.success(request, f'✅ Material "{material.nombre}" creado exitosamente.')
            return redirect('opticut:lista_materiales')
    else:
        form = MaterialForm()
    
    return render(request, 'opticut/crear_material.html', {
        'form': form,
    })


@login_required
def editar_material(request, pk):
    """
    Edita un material existente.
    Permite editar materiales del usuario y materiales predefinidos del sistema.
    """
    # Permitir editar materiales del usuario o predefinidos
    material = get_object_or_404(Material, pk=pk)
    
    # Verificar permisos: solo puede editar si es suyo o es predefinido
    if not material.es_predefinido and material.usuario != request.user:
        messages.error(request, "No tienes permiso para editar este material.")
        return redirect('opticut:lista_materiales')
    
    if request.method == "POST":
        form = MaterialForm(request.POST, instance=material)
        if form.is_valid():
            material_actualizado = form.save(commit=False)
            # Si es predefinido, asegurar que siga siendo predefinido
            if material.es_predefinido:
                material_actualizado.es_predefinido = True
                material_actualizado.usuario = None
            material_actualizado.save()
            messages.success(request, f'✅ Material "{material_actualizado.nombre}" actualizado exitosamente.')
            return redirect('opticut:lista_materiales')
    else:
        form = MaterialForm(instance=material)
    
    return render(request, 'opticut/editar_material.html', {
        'form': form,
        'material': material,
    })


@login_required
def eliminar_material(request, pk):
    """
    Elimina un material (incluyendo predefinidos).
    """
        # Permitir eliminar materiales predefinidos también
    material = get_object_or_404(
        Material,
        Q(pk=pk, usuario=request.user) | Q(pk=pk, es_predefinido=True)
    )
    
    # Verificar que no esté en uso
    optimizaciones_usando = Optimizacion.objects.filter(material=material).count()
    if optimizaciones_usando > 0:
        messages.warning(
            request, 
            f'⚠️ No se puede eliminar el material "{material.nombre}" porque está siendo usado en {optimizaciones_usando} optimización(es).'
        )
        return redirect('opticut:lista_materiales')
    
    if request.method == "POST":
        nombre = material.nombre
        es_predefinido = material.es_predefinido
        material.delete()
        tipo = "predefinido" if es_predefinido else "personal"
        messages.success(request, f'✅ Material {tipo} "{nombre}" eliminado exitosamente.')
        return redirect('opticut:lista_materiales')
    
    return render(request, 'opticut/eliminar_material.html', {
        'material': material,
    })


# ==================== VISTAS DE CLIENTES (FASE 2) ====================

@login_required
def lista_clientes(request):
    """
    Lista todos los clientes del usuario con búsqueda.
    """
    clientes = Cliente.objects.filter(usuario=request.user)
    
    # Búsqueda
    busqueda = request.GET.get('busqueda', '').strip()
    if busqueda:
        clientes = clientes.filter(
            Q(nombre__icontains=busqueda) |
            Q(rut__icontains=busqueda) |
            Q(email__icontains=busqueda)
        )
    
    # Estadísticas
    total_clientes = clientes.count()
    
    return render(request, 'opticut/lista_clientes.html', {
        'clientes': clientes,
        'busqueda': busqueda,
        'total_clientes': total_clientes,
    })


@login_required
def crear_cliente(request):
    """
    Crea un nuevo cliente.
    """
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.usuario = request.user
            cliente.save()
            messages.success(request, f'✅ Cliente "{cliente.nombre}" creado exitosamente.')
            return redirect('opticut:lista_clientes')
    else:
        form = ClienteForm()
    
    return render(request, 'opticut/crear_cliente.html', {
        'form': form,
    })


@login_required
def editar_cliente(request, pk):
    """
    Edita un cliente existente.
    """
    try:
        cliente = Cliente.objects.get(pk=pk, usuario=request.user)
    except Cliente.DoesNotExist:
        messages.error(request, "No se encontró el cliente o no tienes permiso para editarlo.")
        return redirect('opticut:lista_clientes')
    
    if request.method == "POST":
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ Cliente "{cliente.nombre}" actualizado exitosamente.')
            return redirect('opticut:lista_clientes')
    else:
        form = ClienteForm(instance=cliente)
    
    return render(request, 'opticut/editar_cliente.html', {
        'form': form,
        'cliente': cliente,
    })


@login_required
def eliminar_cliente(request, pk):
    """
    Elimina un cliente.
    """
    cliente = get_object_or_404(Cliente, pk=pk, usuario=request.user)
    
    # Verificar que no esté en uso
    optimizaciones_usando = Optimizacion.objects.filter(cliente=cliente, usuario=request.user).count()
    proyectos_usando = Proyecto.objects.filter(cliente=cliente, usuario=request.user).count()
    
    if optimizaciones_usando > 0 or proyectos_usando > 0:
        messages.warning(
            request, 
            f'⚠️ No se puede eliminar el cliente "{cliente.nombre}" porque está siendo usado en {optimizaciones_usando} optimización(es) y {proyectos_usando} proyecto(s).'
        )
        return redirect('opticut:lista_clientes')
        
    if request.method == "POST":
        nombre = cliente.nombre
        cliente.delete()
        messages.success(request, f'✅ Cliente "{nombre}" eliminado exitosamente.')
        return redirect('opticut:lista_clientes')
    
    return render(request, 'opticut/eliminar_cliente.html', {
        'cliente': cliente,
    })


@login_required
def historial_cliente(request, pk):
    """
    Muestra el historial de optimizaciones y proyectos de un cliente.
    """
    cliente = get_object_or_404(Cliente, pk=pk, usuario=request.user)
    
    # Optimizaciones del cliente
    optimizaciones = Optimizacion.objects.filter(cliente=cliente, usuario=request.user).order_by('-fecha')
    
    # Proyectos del cliente
    proyectos = Proyecto.objects.filter(cliente=cliente, usuario=request.user).order_by('-fecha_creacion')
    
    # Estadísticas
    total_optimizaciones = optimizaciones.count()
    total_proyectos = proyectos.count()
    
    # Calcular costo total
    costo_total = Decimal('0.00')
    for opt in optimizaciones:
        costo = opt.get_costo_total()
        if costo:
            costo_total += costo
    
    return render(request, 'opticut/historial_cliente.html', {
        'cliente': cliente,
        'optimizaciones': optimizaciones,
        'proyectos': proyectos,
        'total_optimizaciones': total_optimizaciones,
        'total_proyectos': total_proyectos,
        'costo_total': costo_total,
    })


# ==================== VISTAS DE PRESUPUESTOS (FASE 2) ====================

@login_required
def lista_presupuestos(request):
    """
    Lista todos los presupuestos del usuario.
    """
    # Filtrar presupuestos del usuario
    presupuestos = Presupuesto.objects.filter(
        usuario=request.user
    ).prefetch_related('optimizaciones').select_related('cliente', 'proyecto').order_by('-fecha_creacion')
    
    # Filtros
    estado_filtro = request.GET.get('estado', '')
    if estado_filtro:
        presupuestos = presupuestos.filter(estado=estado_filtro)
    
    # Búsqueda
    busqueda = request.GET.get('busqueda', '').strip()
    if busqueda:
        presupuestos = presupuestos.filter(
            Q(numero__icontains=busqueda) |
            Q(cliente__nombre__icontains=busqueda)
        )
    
    return render(request, 'opticut/lista_presupuestos.html', {
        'presupuestos': presupuestos,
        'estado_filtro': estado_filtro,
        'busqueda': busqueda,
    })


@login_required
def crear_presupuesto(request):
    """
    Crea un nuevo presupuesto desde una optimización.
    """
    # Si viene desde una optimización específica
    optimizacion_id = request.GET.get('optimizacion')
    optimizacion = None
    if optimizacion_id:
        optimizacion = get_object_or_404(Optimizacion, pk=optimizacion_id, usuario=request.user)
    
    if request.method == "POST":
        form = PresupuestoForm(request.POST, user=request.user)
        if form.is_valid():
            presupuesto = form.save(commit=False)
            presupuesto.usuario = request.user
            
            # Manejar nombre de cliente nuevo
            nombre_cliente_nuevo = form.cleaned_data.get('nombre_cliente_nuevo', '').strip()
            if nombre_cliente_nuevo:
                # Buscar o crear cliente con ese nombre
                cliente, created = Cliente.objects.get_or_create(
                    nombre=nombre_cliente_nuevo,
                    usuario=request.user,
                    defaults={'nombre': nombre_cliente_nuevo}
                )
                presupuesto.cliente = cliente
                if created:
                    messages.info(request, f'✅ Cliente "{nombre_cliente_nuevo}" creado automáticamente.')
            elif not presupuesto.cliente:
                # Si no hay cliente seleccionado ni nombre nuevo, usar el de la optimización si existe
                if optimizacion and optimizacion.cliente:
                    presupuesto.cliente = optimizacion.cliente
            
            # Generar número único
            presupuesto.numero = Presupuesto.generar_numero_presupuesto(usuario=request.user)
            
            # Calcular costo_total inicial antes del primer guardado
            # Usar las optimizaciones del formulario para calcular
            optimizaciones_seleccionadas = form.cleaned_data['optimizaciones']
            costo_total_inicial = Decimal('0.00')
            for optimizacion in optimizaciones_seleccionadas:
                num_tableros = optimizacion.num_tableros or 0
                costo_material = presupuesto.precio_tablero * Decimal(str(num_tableros))
                costo_total_inicial += costo_material
            costo_total_inicial += presupuesto.mano_obra
            presupuesto.costo_total = costo_total_inicial
            
            # Guardar primero para poder asignar las optimizaciones ManyToMany
            presupuesto.save()
            
            # Asignar optimizaciones (ManyToMany)
            presupuesto.optimizaciones.set(optimizaciones_seleccionadas)
            
            # Recalcular costo total (por si acaso) y guardar de nuevo
            presupuesto.costo_total = presupuesto.calcular_costo_total_multiple()
            presupuesto.save()
            
            num_optimizaciones = presupuesto.optimizaciones.count()
            
            # Enviar notificación de presupuesto creado (esto mostrará el mensaje según la configuración)
            enviar_notificacion(
                request,
                'presupuesto_creado',
                'Presupuesto Creado',
                f'Se ha creado el presupuesto #{presupuesto.numero} con un costo total de ${presupuesto.costo_total:.2f}.',
                {'presupuesto_id': presupuesto.id, 'numero': presupuesto.numero, 'costo_total': presupuesto.costo_total}
            )
            return redirect('opticut:detalle_presupuesto', pk=presupuesto.pk)
    else:
        form = PresupuestoForm(user=request.user)
        if optimizacion:
            # Prellenar datos desde la optimización
            form.fields['optimizaciones'].initial = [optimizacion]
            if optimizacion.cliente:
                form.fields['cliente'].initial = optimizacion.cliente
            if optimizacion.precio_tablero:
                form.fields['precio_tablero'].initial = optimizacion.precio_tablero
            if optimizacion.mano_obra:
                form.fields['mano_obra'].initial = optimizacion.mano_obra
            if optimizacion.proyecto:
                form.fields['proyecto'].initial = optimizacion.proyecto
    
    # Preparar información adicional de optimizaciones para el template
    optimizaciones_info = []
    optimizaciones_seleccionadas_ids = []
    if optimizacion:
        optimizaciones_seleccionadas_ids = [optimizacion.pk]
    
    if form.fields['optimizaciones'].queryset:
        todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user).order_by('-fecha')
        total_optimizaciones = todas_optimizaciones.count()
        
        for opt in form.fields['optimizaciones'].queryset:
            # Calcular número de lista
            numero_lista = opt.pk
            for idx, optimizacion_lista in enumerate(todas_optimizaciones, start=1):
                if optimizacion_lista.id == opt.id:
                    numero_lista = total_optimizaciones - idx + 1
                    break
            
            # Extraer nombres de piezas
            nombres_piezas = []
            if opt.piezas:
                for linea in opt.piezas.splitlines():
                    if linea.strip():
                        partes = linea.split(',')
                        if len(partes) == 4:  # Formato con nombre: nombre,ancho,alto,cantidad
                            nombre = partes[0].strip()
                            cantidad = int(partes[3].strip())
                            nombres_piezas.append(f"{nombre} (x{cantidad})")
                        elif len(partes) == 3:  # Formato sin nombre: ancho,alto,cantidad
                            cantidad = int(partes[2].strip())
                            nombres_piezas.append(f"Pieza (x{cantidad})")
            
            optimizaciones_info.append({
                'optimizacion': opt,
                'numero_lista': numero_lista,
                'seleccionada': opt.pk in optimizaciones_seleccionadas_ids,
                'nombres_piezas': nombres_piezas[:5],  # Máximo 5 piezas para no hacer muy largo
                'total_piezas': len(nombres_piezas),
            })
    
    return render(request, 'opticut/crear_presupuesto.html', {
        'form': form,
        'optimizacion': optimizacion,
        'optimizaciones_info': optimizaciones_info,
    })


@login_required
def editar_presupuesto(request, pk):
    """
    Edita un presupuesto existente.
    """
    try:
        presupuesto = Presupuesto.objects.prefetch_related('optimizaciones').select_related('cliente', 'proyecto').get(
            pk=pk,
            usuario=request.user
        )
    except Presupuesto.DoesNotExist:
        messages.error(request, "Presupuesto no encontrado.")
        return redirect('opticut:lista_presupuestos')
    
    if request.method == "POST":
        form = PresupuestoForm(request.POST, instance=presupuesto, user=request.user)
        if form.is_valid():
            presupuesto = form.save(commit=False)
            
            # Manejar nombre de cliente nuevo
            nombre_cliente_nuevo = form.cleaned_data.get('nombre_cliente_nuevo', '').strip()
            if nombre_cliente_nuevo:
                # Buscar o crear cliente con ese nombre
                cliente, created = Cliente.objects.get_or_create(
                    nombre=nombre_cliente_nuevo,
                    usuario=request.user,
                    defaults={'nombre': nombre_cliente_nuevo}
                )
                presupuesto.cliente = cliente
                if created:
                    messages.info(request, f'✅ Cliente "{nombre_cliente_nuevo}" creado automáticamente.')
            
            # Guardar primero para poder asignar las optimizaciones ManyToMany
            presupuesto.save()
            
            # Asignar optimizaciones (ManyToMany)
            optimizaciones_seleccionadas = form.cleaned_data['optimizaciones']
            presupuesto.optimizaciones.set(optimizaciones_seleccionadas)
            
            # Recalcular costo total y guardar de nuevo
            presupuesto.costo_total = presupuesto.calcular_costo_total_multiple()
            presupuesto.save()
            
            num_optimizaciones = presupuesto.optimizaciones.count()
            messages.success(request, f'✅ Presupuesto "{presupuesto.numero}" actualizado exitosamente con {num_optimizaciones} optimización(es).')
            return redirect('opticut:detalle_presupuesto', pk=presupuesto.pk)
    else:
        form = PresupuestoForm(instance=presupuesto, user=request.user)
    
    # Preparar información adicional de optimizaciones para el template
    optimizaciones_info = []
    optimizaciones_seleccionadas_ids = list(presupuesto.optimizaciones.values_list('pk', flat=True))
    
    if form.fields['optimizaciones'].queryset:
        todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user).order_by('-fecha')
        total_optimizaciones = todas_optimizaciones.count()
        
        for opt in form.fields['optimizaciones'].queryset:
            # Calcular número de lista
            numero_lista = opt.pk
            for idx, optimizacion_lista in enumerate(todas_optimizaciones, start=1):
                if optimizacion_lista.id == opt.id:
                    numero_lista = total_optimizaciones - idx + 1
                    break
            
            # Extraer nombres de piezas
            nombres_piezas = []
            if opt.piezas:
                for linea in opt.piezas.splitlines():
                    if linea.strip():
                        partes = linea.split(',')
                        if len(partes) == 4:  # Formato con nombre: nombre,ancho,alto,cantidad
                            nombre = partes[0].strip()
                            cantidad = int(partes[3].strip())
                            nombres_piezas.append(f"{nombre} (x{cantidad})")
                        elif len(partes) == 3:  # Formato sin nombre: ancho,alto,cantidad
                            cantidad = int(partes[2].strip())
                            nombres_piezas.append(f"Pieza (x{cantidad})")
            
            optimizaciones_info.append({
                'optimizacion': opt,
                'numero_lista': numero_lista,
                'seleccionada': opt.pk in optimizaciones_seleccionadas_ids,
                'nombres_piezas': nombres_piezas[:5],  # Máximo 5 piezas para no hacer muy largo
                'total_piezas': len(nombres_piezas),
            })
    
    return render(request, 'opticut/editar_presupuesto.html', {
        'form': form,
        'presupuesto': presupuesto,
        'optimizaciones_info': optimizaciones_info,
    })


@login_required
def detalle_presupuesto(request, pk):
    """
    Muestra el detalle de un presupuesto y permite generar PDF.
    """
    try:
        presupuesto = Presupuesto.objects.prefetch_related('optimizaciones').select_related('cliente', 'proyecto').get(
            pk=pk,
            usuario=request.user
        )
    except Presupuesto.DoesNotExist:
        messages.error(request, "Presupuesto no encontrado.")
        return redirect('opticut:lista_presupuestos')
    
    # Calcular información adicional para el template
    # Obtener todas las optimizaciones del usuario ordenadas por fecha descendente (igual que en historial)
    todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user).order_by('-fecha')
    total_optimizaciones = todas_optimizaciones.count()
    
    optimizaciones_con_costos = []
    for opt in presupuesto.optimizaciones.all():
        num_tableros = opt.num_tableros or 0
        costo_tableros = presupuesto.precio_tablero * Decimal(str(num_tableros))
        
        # Calcular el número de lista (basado en orden por fecha descendente)
        numero_lista = opt.pk  # Por defecto usar el ID
        for idx, optimizacion in enumerate(todas_optimizaciones, start=1):
            if optimizacion.id == opt.id:
                # Para orden descendente: numero = total - idx + 1
                numero_lista = total_optimizaciones - idx + 1
                break
        
        optimizaciones_con_costos.append({
            'optimizacion': opt,
            'num_tableros': num_tableros,
            'costo_tableros': costo_tableros,
            'numero_lista': numero_lista,
        })
    
    return render(request, 'opticut/detalle_presupuesto.html', {
        'presupuesto': presupuesto,
        'optimizaciones_con_costos': optimizaciones_con_costos,
        'total_tableros': presupuesto.get_total_tableros(),
    })


@login_required
def generar_pdf_presupuesto(request, pk):
    """
    Genera el PDF del presupuesto.
    """
    try:
        presupuesto = Presupuesto.objects.prefetch_related('optimizaciones').select_related('cliente').get(
            pk=pk,
            usuario=request.user
        )
    except Presupuesto.DoesNotExist:
        messages.error(request, "Presupuesto no encontrado.")
        return redirect('opticut:lista_presupuestos')
    
    # Generar PDF usando la función de utils
    from .utils import generar_pdf_presupuesto as generar_pdf_func
    pdf_path = generar_pdf_func(presupuesto)
    
    if pdf_path:
        presupuesto.pdf = pdf_path
        presupuesto.save()
        return FileResponse(open(pdf_path, 'rb'), content_type='application/pdf', filename=f'presupuesto_{presupuesto.numero}.pdf')
    else:
        messages.error(request, "Error al generar el PDF del presupuesto.")
        return redirect('opticut:detalle_presupuesto', pk=presupuesto.pk)


@login_required
def agregar_optimizaciones_presupuesto(request, pk):
    """
    Permite agregar múltiples optimizaciones a un presupuesto existente.
    """
    try:
        presupuesto = Presupuesto.objects.prefetch_related('optimizaciones').get(
            pk=pk,
            usuario=request.user
        )
    except Presupuesto.DoesNotExist:
        messages.error(request, "Presupuesto no encontrado.")
        return redirect('opticut:lista_presupuestos')
    
    # Obtener optimizaciones que aún no están en el presupuesto
    optimizaciones_en_presupuesto = presupuesto.optimizaciones.values_list('pk', flat=True)
    optimizaciones_disponibles = Optimizacion.objects.filter(
        usuario=request.user
    ).exclude(pk__in=optimizaciones_en_presupuesto).order_by('-fecha')
    
    if request.method == "POST":
        optimizaciones_ids = request.POST.getlist('optimizaciones')
        if optimizaciones_ids:
            optimizaciones_seleccionadas = Optimizacion.objects.filter(
                pk__in=optimizaciones_ids,
                usuario=request.user
            )
            # Agregar las optimizaciones al presupuesto (ManyToMany)
            presupuesto.optimizaciones.add(*optimizaciones_seleccionadas)
            
            # Recalcular costo total
            presupuesto.costo_total = presupuesto.calcular_costo_total_multiple()
            presupuesto.save()
            
            messages.success(
                request, 
                f'✅ {optimizaciones_seleccionadas.count()} optimización(es) agregada(s) al presupuesto "{presupuesto.numero}".'
            )
            return redirect('opticut:detalle_presupuesto', pk=presupuesto.pk)
        else:
            messages.warning(request, "Debes seleccionar al menos una optimización.")
    
    return render(request, 'opticut/agregar_optimizaciones_presupuesto.html', {
        'presupuesto': presupuesto,
        'optimizaciones_disponibles': optimizaciones_disponibles,
    })


@login_required
def historial_costos(request):
    """
    Vista de historial de costos con gráficos y filtros por fecha.
    Soporta exportación a Excel.
    """
    # Obtener todas las optimizaciones con costos del usuario
    optimizaciones = Optimizacion.objects.filter(usuario=request.user).exclude(
        precio_tablero__isnull=True
    ).order_by('-fecha')
    
    # Filtros por fecha
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
    
    # Calcular estadísticas
    total_optimizaciones = optimizaciones.count()
    costo_total = Decimal('0.00')
    costo_material_total = Decimal('0.00')
    costo_mano_obra_total = Decimal('0.00')
    num_tableros_total = 0
    aprovechamiento_total = Decimal('0.00')
    
    optimizaciones_con_costo = []
    for opt in optimizaciones:
        costo = opt.get_costo_total()
        if costo:
            costo_total += costo
            costo_material = Decimal(str(opt.num_tableros or 0)) * opt.precio_tablero if opt.precio_tablero else Decimal('0.00')
            costo_material_total += costo_material
            costo_mano_obra_total += opt.mano_obra
            num_tableros_total += opt.num_tableros or 0
            aprovechamiento_total += Decimal(str(opt.aprovechamiento_total or 0))
            
            optimizaciones_con_costo.append({
                'optimizacion': opt,
                'costo_total': costo,
                'costo_material': costo_material,
                'costo_mano_obra': opt.mano_obra,
            })
    
    # Calcular estadísticas adicionales
    costo_promedio = costo_total / total_optimizaciones if total_optimizaciones > 0 else Decimal('0.00')
    costo_por_tablero = costo_total / num_tableros_total if num_tableros_total > 0 else Decimal('0.00')
    porcentaje_material = (costo_material_total / costo_total * 100) if costo_total > 0 else Decimal('0.00')
    porcentaje_mano_obra = (costo_mano_obra_total / costo_total * 100) if costo_total > 0 else Decimal('0.00')
    aprovechamiento_promedio = aprovechamiento_total / total_optimizaciones if total_optimizaciones > 0 else Decimal('0.00')
    
    # Verificar si se solicita exportación a Excel
    if request.GET.get('export') == 'excel':
        from .utils import generar_excel_historial_costos
        from django.http import HttpResponse
        
        estadisticas = {
            'total_optimizaciones': total_optimizaciones,
            'costo_total': float(costo_total),
            'costo_material_total': float(costo_material_total),
            'costo_mano_obra_total': float(costo_mano_obra_total),
            'num_tableros_total': num_tableros_total,
            'costo_promedio': float(costo_promedio),
            'costo_por_tablero': float(costo_por_tablero),
            'porcentaje_material': float(porcentaje_material),
            'porcentaje_mano_obra': float(porcentaje_mano_obra),
            'aprovechamiento_promedio': float(aprovechamiento_promedio),
        }
        
        excel_buffer = generar_excel_historial_costos(
            optimizaciones_con_costo,
            estadisticas,
            fecha_desde=fecha_desde if fecha_desde else None,
            fecha_hasta=fecha_hasta if fecha_hasta else None
        )
        
        # Generar nombre de archivo
        from datetime import datetime
        fecha_actual = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_archivo = f"historial_costos_{fecha_actual}.xlsx"
        
        response = HttpResponse(
            excel_buffer.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        
        return response
    
    # Generar gráfico de costos por fecha
    grafico_costos_base64 = None
    if optimizaciones_con_costo:
        fechas = [opt['optimizacion'].fecha.date() for opt in optimizaciones_con_costo]
        costos = [float(opt['costo_total']) for opt in optimizaciones_con_costo]
        
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from io import BytesIO
        import base64
        
        plt.figure(figsize=(12, 6))
        plt.plot(fechas, costos, marker='o', linestyle='-', linewidth=2, markersize=6)
        plt.title('Evolución de Costos', fontsize=16, fontweight='bold')
        plt.xlabel('Fecha', fontsize=12)
        plt.ylabel('Costo Total ($)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.gcf().autofmt_xdate()
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        grafico_costos_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close()
        buffer.close()
    
    return render(request, 'opticut/historial_costos.html', {
        'optimizaciones_con_costo': optimizaciones_con_costo,
        'total_optimizaciones': total_optimizaciones,
        'costo_total': costo_total,
        'costo_material_total': costo_material_total,
        'costo_mano_obra_total': costo_mano_obra_total,
        'num_tableros_total': num_tableros_total,
        'costo_promedio': costo_promedio,
        'costo_por_tablero': costo_por_tablero,
        'porcentaje_material': porcentaje_material,
        'porcentaje_mano_obra': porcentaje_mano_obra,
        'aprovechamiento_promedio': aprovechamiento_promedio,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'grafico_costos_base64': grafico_costos_base64,
    })


# ==================== VISTAS DE PROYECTOS (FASE 3) ====================

@login_required
def lista_proyectos(request):
    """
    Lista todos los proyectos del usuario con filtros y búsqueda.
    """
    proyectos = Proyecto.objects.filter(usuario=request.user).select_related('cliente').order_by('-fecha_creacion')
    
    # Filtros
    estado_filtro = request.GET.get('estado', '')
    if estado_filtro:
        proyectos = proyectos.filter(estado=estado_filtro)
    
    # Búsqueda
    busqueda = request.GET.get('busqueda', '').strip()
    if busqueda:
        proyectos = proyectos.filter(
            Q(nombre__icontains=busqueda) |
            Q(descripcion__icontains=busqueda) |
            Q(cliente__nombre__icontains=busqueda)
        )
    
    return render(request, 'opticut/lista_proyectos.html', {
        'proyectos': proyectos,
        'estado_filtro': estado_filtro,
        'busqueda': busqueda,
    })


@login_required
def crear_proyecto(request):
    """
    Crea un nuevo proyecto con opción de agregar optimizaciones.
    """
    if request.method == "POST":
        form = ProyectoForm(request.POST, user=request.user)
        if form.is_valid():
            proyecto = form.save(commit=False)
            proyecto.usuario = request.user
            proyecto.save()
            
            # Asignar optimizaciones seleccionadas al proyecto
            optimizaciones_seleccionadas = form.cleaned_data.get('optimizaciones', [])
            if optimizaciones_seleccionadas:
                # Obtener IDs de las optimizaciones seleccionadas
                optimizaciones_ids = [opt.pk for opt in optimizaciones_seleccionadas]
                # Verificar que las optimizaciones pertenezcan al usuario y asignarlas
                optimizaciones_validas = Optimizacion.objects.filter(
                    pk__in=optimizaciones_ids,
                    usuario=request.user
                )
                optimizaciones_validas.update(proyecto=proyecto)
                num_optimizaciones = optimizaciones_validas.count()
                mensaje_proyecto = f'Se ha creado el proyecto "{proyecto.nombre}" exitosamente con {num_optimizaciones} optimización(es) asociada(s).'
            else:
                mensaje_proyecto = f'Se ha creado el proyecto "{proyecto.nombre}" exitosamente.'
            
            # Enviar notificación de proyecto creado (esto mostrará el mensaje según la configuración)
            enviar_notificacion(
                request,
                'proyecto_creado',
                'Proyecto Creado',
                mensaje_proyecto,
                {'proyecto_id': proyecto.id, 'nombre': proyecto.nombre}
            )
            
            return redirect('opticut:detalle_proyecto', pk=proyecto.pk)
    else:
        form = ProyectoForm(user=request.user)
    
    # Preparar información adicional de optimizaciones para el template
    optimizaciones_info = []
    optimizaciones_seleccionadas_ids = []
    
    if form.fields['optimizaciones'].queryset:
        todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user).order_by('-fecha')
        total_optimizaciones = todas_optimizaciones.count()
        
        for opt in form.fields['optimizaciones'].queryset:
            # Calcular número de lista
            numero_lista = opt.pk
            for idx, optimizacion_lista in enumerate(todas_optimizaciones, start=1):
                if optimizacion_lista.id == opt.id:
                    numero_lista = total_optimizaciones - idx + 1
                    break
            
            # Extraer nombres de piezas
            nombres_piezas = []
            if opt.piezas:
                for linea in opt.piezas.splitlines():
                    if linea.strip():
                        partes = linea.split(',')
                        if len(partes) == 4:  # Formato con nombre: nombre,ancho,alto,cantidad
                            nombre = partes[0].strip()
                            cantidad = int(partes[3].strip())
                            nombres_piezas.append(f"{nombre} (x{cantidad})")
                        elif len(partes) == 3:  # Formato sin nombre: ancho,alto,cantidad
                            cantidad = int(partes[2].strip())
                            nombres_piezas.append(f"Pieza (x{cantidad})")
            
            optimizaciones_info.append({
                'optimizacion': opt,
                'numero_lista': numero_lista,
                'seleccionada': opt.pk in optimizaciones_seleccionadas_ids,
                'nombres_piezas': nombres_piezas[:5],  # Máximo 5 piezas para no hacer muy largo
                'total_piezas': len(nombres_piezas),
            })
    
    return render(request, 'opticut/crear_proyecto.html', {
        'form': form,
        'optimizaciones_info': optimizaciones_info,
    })


@login_required
def detalle_proyecto(request, pk):
    """
    Muestra el detalle de un proyecto con sus optimizaciones y métricas.
    """
    try:
        proyecto = Proyecto.objects.select_related('cliente').get(
            pk=pk,
            usuario=request.user
        )
    except Proyecto.DoesNotExist:
        messages.error(request, "Proyecto no encontrado.")
        return redirect('opticut:lista_proyectos')
    
    # Optimizaciones del proyecto
    optimizaciones = Optimizacion.objects.filter(proyecto=proyecto, usuario=request.user).order_by('-fecha')
    
    # Estadísticas
    total_optimizaciones = optimizaciones.count()
    costo_total = proyecto.get_total_costo()
    
    # Calcular promedio de aprovechamiento
    aprovechamiento_promedio = optimizaciones.aggregate(
        promedio=Avg('aprovechamiento_total')
    )['promedio'] or 0
    
    # Total de tableros
    total_tableros = sum(opt.num_tableros or 0 for opt in optimizaciones)
    
    return render(request, 'opticut/detalle_proyecto.html', {
        'proyecto': proyecto,
        'optimizaciones': optimizaciones,
        'total_optimizaciones': total_optimizaciones,
        'costo_total': costo_total,
        'aprovechamiento_promedio': aprovechamiento_promedio,
        'total_tableros': total_tableros,
    })


@login_required
def editar_proyecto(request, pk):
    """
    Edita un proyecto existente.
    """
    proyecto = get_object_or_404(Proyecto, pk=pk, usuario=request.user)
    
    if request.method == "POST":
        form = ProyectoForm(request.POST, instance=proyecto, user=request.user)
        if form.is_valid():
            proyecto = form.save(commit=False)
            proyecto.save()
            
            # Actualizar optimizaciones seleccionadas
            optimizaciones_seleccionadas = form.cleaned_data.get('optimizaciones', [])
            optimizaciones_seleccionadas_ids = [opt.pk for opt in optimizaciones_seleccionadas]
            
            # Primero, quitar el proyecto de todas las optimizaciones que ya no están seleccionadas
            optimizaciones_actuales = proyecto.optimizacion_set.all()
            for opt in optimizaciones_actuales:
                if opt.pk not in optimizaciones_seleccionadas_ids:
                    opt.proyecto = None
                    opt.save()
            
            # Luego, asignar el proyecto a las optimizaciones seleccionadas
            if optimizaciones_seleccionadas_ids:
                Optimizacion.objects.filter(
                    pk__in=optimizaciones_seleccionadas_ids,
                    usuario=request.user
                ).update(proyecto=proyecto)
            
            messages.success(request, f'✅ Proyecto "{proyecto.nombre}" actualizado exitosamente.')
            return redirect('opticut:detalle_proyecto', pk=proyecto.pk)
    else:
        form = ProyectoForm(instance=proyecto, user=request.user)
    
    # Preparar información adicional de optimizaciones para el template
    optimizaciones_info = []
    optimizaciones_seleccionadas_ids = list(proyecto.optimizacion_set.values_list('pk', flat=True))
    
    if form.fields['optimizaciones'].queryset:
        todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user).order_by('-fecha')
        total_optimizaciones = todas_optimizaciones.count()
        
        for opt in form.fields['optimizaciones'].queryset:
            # Calcular número de lista
            numero_lista = opt.pk
            for idx, optimizacion_lista in enumerate(todas_optimizaciones, start=1):
                if optimizacion_lista.id == opt.id:
                    numero_lista = total_optimizaciones - idx + 1
                    break
            
            # Extraer nombres de piezas
            nombres_piezas = []
            if opt.piezas:
                for linea in opt.piezas.splitlines():
                    if linea.strip():
                        partes = linea.split(',')
                        if len(partes) == 4:  # Formato con nombre: nombre,ancho,alto,cantidad
                            nombre = partes[0].strip()
                            cantidad = int(partes[3].strip())
                            nombres_piezas.append(f"{nombre} (x{cantidad})")
                        elif len(partes) == 3:  # Formato sin nombre: ancho,alto,cantidad
                            cantidad = int(partes[2].strip())
                            nombres_piezas.append(f"Pieza (x{cantidad})")
            
            optimizaciones_info.append({
                'optimizacion': opt,
                'numero_lista': numero_lista,
                'seleccionada': opt.pk in optimizaciones_seleccionadas_ids,
                'nombres_piezas': nombres_piezas[:5],  # Máximo 5 piezas para no hacer muy largo
                'total_piezas': len(nombres_piezas),
            })
    
    return render(request, 'opticut/editar_proyecto.html', {
        'form': form,
        'proyecto': proyecto,
        'optimizaciones_info': optimizaciones_info,
    })


@login_required
def eliminar_proyecto(request, pk):
    """
    Elimina un proyecto.
    """
    try:
        proyecto = Proyecto.objects.get(pk=pk, usuario=request.user)
    except Proyecto.DoesNotExist:
        messages.error(request, "No se encontró el proyecto.")
        return redirect('opticut:lista_proyectos')
    
    optimizaciones_count = proyecto.get_total_optimizaciones()
    
    if request.method == "POST":
        accion = request.POST.get('accion', 'mover')
        
        if accion == 'eliminar':
            # Eliminar todas las optimizaciones del proyecto
            proyecto.optimizacion_set.all().delete()
        # Si es 'mover', las optimizaciones simplemente perderán la referencia al proyecto (SET_NULL)
        
        nombre = proyecto.nombre
        proyecto.delete()
        messages.success(request, f'✅ Proyecto "{nombre}" eliminado exitosamente.')
        return redirect('opticut:lista_proyectos')
    
    return render(request, 'opticut/eliminar_proyecto.html', {
        'proyecto': proyecto,
        'optimizaciones_count': optimizaciones_count,
    })


# ==================== COMPARACIÓN DE OPTIMIZACIONES (FASE 3) ====================

@login_required
def agregar_optimizaciones_proyecto(request, pk):
    """
    Permite agregar múltiples optimizaciones a un proyecto existente.
    """
    proyecto = get_object_or_404(Proyecto, pk=pk, usuario=request.user)
    
    # Obtener optimizaciones que aún no están en el proyecto
    optimizaciones_en_proyecto = proyecto.optimizacion_set.values_list('pk', flat=True)
    optimizaciones_disponibles = Optimizacion.objects.filter(
        usuario=request.user
    ).exclude(pk__in=optimizaciones_en_proyecto).order_by('-fecha')
    
    if request.method == "POST":
        optimizaciones_ids = request.POST.getlist('optimizaciones')
        if optimizaciones_ids:
            optimizaciones_seleccionadas = Optimizacion.objects.filter(
                pk__in=optimizaciones_ids,
                usuario=request.user
            )
            # Asignar el proyecto a las optimizaciones seleccionadas
            optimizaciones_seleccionadas.update(proyecto=proyecto)
            
            messages.success(
                request, 
                f'✅ {optimizaciones_seleccionadas.count()} optimización(es) agregada(s) al proyecto "{proyecto.nombre}".'
            )
            return redirect('opticut:detalle_proyecto', pk=proyecto.pk)
        else:
            messages.warning(request, "Debes seleccionar al menos una optimización.")
    
    return render(request, 'opticut/agregar_optimizaciones_proyecto.html', {
        'proyecto': proyecto,
        'optimizaciones_disponibles': optimizaciones_disponibles,
    })


@login_required
def comparar_optimizaciones(request):
    """
    Vista para seleccionar y comparar dos optimizaciones lado a lado.
    """
    optimizaciones = Optimizacion.objects.filter(usuario=request.user).order_by('-fecha')
    
    # Si se seleccionaron dos optimizaciones para comparar
    opt1_id = request.GET.get('opt1')
    opt2_id = request.GET.get('opt2')
    
    optimizacion1 = None
    optimizacion2 = None
    
    # Calcular diferencias y desperdicios
    diferencia_aprovechamiento = None
    diferencia_tableros = None
    diferencia_desperdicio = None
    desperdicio1 = None
    desperdicio2 = None
    
    if opt1_id and opt2_id:
        try:
            optimizacion1 = Optimizacion.objects.get(pk=opt1_id, usuario=request.user)
            optimizacion2 = Optimizacion.objects.get(pk=opt2_id, usuario=request.user)
            
            # Calcular num_tableros si no está guardado (para optimizaciones antiguas)
            def obtener_num_tableros(optimizacion):
                """Obtiene el número de tableros, calculándolo si no está guardado"""
                if optimizacion.num_tableros and optimizacion.num_tableros > 0:
                    return optimizacion.num_tableros
                
                # Si no está guardado, calcularlo desde las piezas
                try:
                    piezas_list = []
                    for linea in optimizacion.piezas.splitlines():
                        if linea.strip():
                            partes = linea.split(',')
                            if len(partes) >= 3:
                                cantidad = int(partes[-1]) if len(partes) >= 4 else int(partes[2])
                                ancho_idx = 1 if len(partes) >= 4 else 0
                                alto_idx = 2 if len(partes) >= 4 else 1
                                ancho = float(partes[ancho_idx])
                                alto = float(partes[alto_idx])
                                # Convertir a cm si es necesario
                                unidad = getattr(optimizacion, 'unidad_medida', 'cm') or 'cm'
                                ancho_cm = convertir_a_cm(ancho, unidad)
                                alto_cm = convertir_a_cm(alto, unidad)
                                for _ in range(cantidad):
                                    piezas_list.append((ancho_cm, alto_cm))
                    
                    if piezas_list:
                        # Usar la función generar_grafico para calcular num_tableros
                        margen = getattr(optimizacion, 'margen_corte', 0.3) or 0.3
                        permitir_rot = getattr(optimizacion, 'permitir_rotacion', True)
                        resultado = generar_grafico(
                            piezas_list,
                            optimizacion.ancho_tablero,
                            optimizacion.alto_tablero,
                            unidad='cm',
                            permitir_rotacion=permitir_rot,
                            margen_corte=margen
                        )
                        return len(resultado['imagenes'])
                except Exception:
                    pass
                
                # Fallback: estimar desde el área
                try:
                    area_tablero = optimizacion.ancho_tablero * optimizacion.alto_tablero
                    area_total = 0
                    for linea in optimizacion.piezas.splitlines():
                        if linea.strip():
                            partes = linea.split(',')
                            if len(partes) >= 3:
                                cantidad = int(partes[-1]) if len(partes) >= 4 else int(partes[2])
                                ancho_idx = 1 if len(partes) >= 4 else 0
                                alto_idx = 2 if len(partes) >= 4 else 1
                                ancho = float(partes[ancho_idx])
                                alto = float(partes[alto_idx])
                                unidad = getattr(optimizacion, 'unidad_medida', 'cm') or 'cm'
                                ancho_cm = convertir_a_cm(ancho, unidad)
                                alto_cm = convertir_a_cm(alto, unidad)
                                area_total += (ancho_cm * alto_cm) * cantidad
                    if area_tablero > 0:
                        return max(1, int(area_total / area_tablero) + 1)
                except Exception:
                    pass
                
                return 1  # Valor por defecto
            
            num_tableros1 = obtener_num_tableros(optimizacion1)
            num_tableros2 = obtener_num_tableros(optimizacion2)
            
            # Actualizar num_tableros si estaba en 0 (para guardarlo en la BD)
            if optimizacion1.num_tableros == 0 and num_tableros1 > 0:
                optimizacion1.num_tableros = num_tableros1
                optimizacion1.save(update_fields=['num_tableros'])
            if optimizacion2.num_tableros == 0 and num_tableros2 > 0:
                optimizacion2.num_tableros = num_tableros2
                optimizacion2.save(update_fields=['num_tableros'])
            
            # Calcular diferencias
            diferencia_aprovechamiento = optimizacion2.aprovechamiento_total - optimizacion1.aprovechamiento_total
            diferencia_tableros = num_tableros2 - num_tableros1
            
            # Calcular desperdicios (100% - aprovechamiento)
            desperdicio1 = 100 - optimizacion1.aprovechamiento_total
            desperdicio2 = 100 - optimizacion2.aprovechamiento_total
            diferencia_desperdicio = desperdicio2 - desperdicio1
            
        except Optimizacion.DoesNotExist:
            messages.error(request, "Una o ambas optimizaciones no fueron encontradas.")
            return redirect('opticut:comparar_optimizaciones')
    
    return render(request, 'opticut/comparar_optimizaciones.html', {
        'optimizaciones': optimizaciones,
        'optimizacion1': optimizacion1,
        'optimizacion2': optimizacion2,
        'diferencia_aprovechamiento': diferencia_aprovechamiento,
        'diferencia_tableros': diferencia_tableros,
        'diferencia_desperdicio': diferencia_desperdicio,
        'desperdicio1': desperdicio1,
        'desperdicio2': desperdicio2,
    })


# ==================== VISTAS DE PLANTILLAS (FASE 4) ====================

@login_required
def lista_plantillas(request):
    """
    Lista todas las plantillas del usuario y las predefinidas del sistema.
    """
    # Plantillas del usuario
    plantillas_usuario = Plantilla.objects.filter(usuario=request.user, es_predefinida=False)
    
    # Plantillas predefinidas del sistema
    plantillas_sistema = Plantilla.objects.filter(es_predefinida=True)
    
    # Búsqueda
    busqueda = request.GET.get('busqueda', '').strip()
    categoria_filtro = request.GET.get('categoria', '')
    
    if busqueda:
        plantillas_usuario = plantillas_usuario.filter(nombre__icontains=busqueda)
        plantillas_sistema = plantillas_sistema.filter(nombre__icontains=busqueda)
    
    if categoria_filtro:
        plantillas_usuario = plantillas_usuario.filter(categoria=categoria_filtro)
        plantillas_sistema = plantillas_sistema.filter(categoria=categoria_filtro)
    
    return render(request, 'opticut/lista_plantillas.html', {
        'plantillas_usuario': plantillas_usuario,
        'plantillas_sistema': plantillas_sistema,
        'busqueda': busqueda,
        'categoria_filtro': categoria_filtro,
    })


@login_required
def crear_plantilla(request):
    """
    Crea una nueva plantilla desde una optimización o desde cero.
    """
    # Si viene desde una optimización específica
    optimizacion_id = request.GET.get('optimizacion')
    optimizacion = None
    if optimizacion_id:
        optimizacion = get_object_or_404(Optimizacion, pk=optimizacion_id, usuario=request.user)
    
    if request.method == "POST":
        form = PlantillaForm(request.POST)
        if form.is_valid():
            plantilla = form.save(commit=False)
            plantilla.usuario = request.user
            plantilla.es_predefinida = False
            plantilla.save()
            messages.success(request, f'✅ Plantilla "{plantilla.nombre}" creada exitosamente.')
            return redirect('opticut:lista_plantillas')
    else:
        form = PlantillaForm()
        if optimizacion:
            # Prellenar datos desde la optimización
            unidad_opt = getattr(optimizacion, 'unidad_medida', 'cm') or 'cm'
            ancho_mostrar = convertir_desde_cm(optimizacion.ancho_tablero, unidad_opt)
            alto_mostrar = convertir_desde_cm(optimizacion.alto_tablero, unidad_opt)
            margen_mm = round(getattr(optimizacion, 'margen_corte', 0.3) * 10, 1)
            
            form.fields['nombre'].initial = f"Plantilla de {optimizacion.fecha.strftime('%d/%m/%Y')}"
            form.fields['ancho_tablero'].initial = ancho_mostrar
            form.fields['alto_tablero'].initial = alto_mostrar
            form.fields['unidad_medida'].initial = unidad_opt
            form.fields['piezas'].initial = optimizacion.piezas
            form.fields['permitir_rotacion'].initial = optimizacion.permitir_rotacion
            form.fields['margen_corte'].initial = margen_mm
    
    return render(request, 'opticut/crear_plantilla.html', {
        'form': form,
        'optimizacion': optimizacion,
    })


@login_required
def editar_plantilla(request, pk):
    """
    Edita una plantilla existente.
    """
    plantilla = get_object_or_404(Plantilla, pk=pk)
    
    # Verificar permisos: solo puede editar si es suya o es predefinida
    if not plantilla.es_predefinida and plantilla.usuario != request.user:
        messages.error(request, "No tienes permiso para editar esta plantilla.")
        return redirect('opticut:lista_plantillas')
    
    if request.method == "POST":
        form = PlantillaForm(request.POST, instance=plantilla)
        if form.is_valid():
            plantilla_actualizada = form.save(commit=False)
            # Si es predefinida, asegurar que siga siendo predefinida
            if plantilla.es_predefinida:
                plantilla_actualizada.es_predefinida = True
                plantilla_actualizada.usuario = None
            plantilla_actualizada.save()
            messages.success(request, f'✅ Plantilla "{plantilla_actualizada.nombre}" actualizada exitosamente.')
            return redirect('opticut:lista_plantillas')
    else:
        form = PlantillaForm(instance=plantilla)
        # Convertir margen de corte de cm a mm para mostrar
        if plantilla.margen_corte:
            form.fields['margen_corte'].initial = round(plantilla.margen_corte * 10, 1)
    
    return render(request, 'opticut/editar_plantilla.html', {
        'form': form,
        'plantilla': plantilla,
    })


@login_required
def eliminar_plantilla(request, pk):
    """
    Elimina una plantilla.
    """
    plantilla = get_object_or_404(Plantilla, pk=pk, usuario=request.user, es_predefinida=False)
    
    if request.method == "POST":
        nombre = plantilla.nombre
        plantilla.delete()
        messages.success(request, f'✅ Plantilla "{nombre}" eliminada exitosamente.')
        return redirect('opticut:lista_plantillas')
    
    return render(request, 'opticut/eliminar_plantilla.html', {
        'plantilla': plantilla,
    })


@login_required
def usar_plantilla(request, pk):
    """
    Carga una plantilla en el formulario de optimización.
    """
    plantilla = get_object_or_404(Plantilla, pk=pk)
    
    # Verificar permisos: solo puede usar si es suya o es predefinida
    if not plantilla.es_predefinida and plantilla.usuario != request.user:
        messages.error(request, "No tienes permiso para usar esta plantilla.")
        return redirect('opticut:lista_plantillas')
    
    # Convertir dimensiones a la unidad de la plantilla
    unidad = plantilla.unidad_medida
    ancho_mostrar = convertir_desde_cm(plantilla.ancho_tablero, unidad)
    alto_mostrar = convertir_desde_cm(plantilla.alto_tablero, unidad)
    margen_mm = round(plantilla.margen_corte * 10, 1)
    
    # Preparar formulario con datos de la plantilla
    from .forms import PiezaForm
    from django.forms import formset_factory
    PiezaFormSet = formset_factory(PiezaForm, extra=0, max_num=20)
    
    piezas_data = plantilla.get_piezas_list()
    pieza_formset = PiezaFormSet(initial=piezas_data)
    
    tablero_form = TableroForm(user=request.user, initial={
        'ancho': ancho_mostrar,
        'alto': alto_mostrar,
        'unidad_medida': unidad,
        'permitir_rotacion': plantilla.permitir_rotacion,
        'margen_corte': margen_mm,
    })
    
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
    
    messages.info(request, f'📋 Plantilla "{plantilla.nombre}" cargada. Completa los datos y genera la optimización.')
    
    return render(request, 'opticut/index.html', {
        'tablero_form': tablero_form,
        'pieza_formset': pieza_formset,
        'materiales_data_json': materiales_data_json,
        'plantilla_cargada': plantilla,
    })


# Handlers de error personalizados
def handler404(request, exception):
    """Maneja errores 404 con una página personalizada"""
    return render(request, 'opticut/404.html', status=404)


def handler500(request):
    """Maneja errores 500 con una página personalizada"""
    return render(request, 'opticut/500.html', status=500)