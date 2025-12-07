from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory
from django.core.files.base import ContentFile
from .forms import TableroForm, PiezaForm
from .models import Optimizacion
from .utils import generar_grafico, generar_pdf, generar_grafico_aprovechamiento, generar_grafico_desperdicio, convertir_a_cm, convertir_desde_cm, obtener_simbolo_unidad, obtener_simbolo_area
import base64
from django.contrib import messages
from django.http import FileResponse
from django.db.models import Avg, Count, Sum, Max, Min
from django.utils import timezone
from datetime import timedelta
import os
from opti import settings

@login_required
def index(request):
    # Limpiar mensajes antiguos al cargar el formulario por primera vez
    if request.method == "GET":
        storage = messages.get_messages(request)
        storage.used = True
    
    PiezaFormSet = formset_factory(PiezaForm, extra=3, max_num=20, validate_max=True)

    if request.method == "POST":
        tablero_form = TableroForm(request.POST)
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
                            return render(request, "opticut/index.html", {
                                "tablero_form": tablero_form,
                                "pieza_formset": pieza_formset
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
                return render(request, "opticut/index.html", {
                    "tablero_form": tablero_form,
                    "pieza_formset": pieza_formset
                })

            # Generar TODAS las imágenes, aprovechamiento Y desperdicio
            imagenes_base64, aprovechamiento, info_desperdicio = generar_grafico(piezas, ancho, alto, unidad)
            
            # Usar la primera imagen para vista previa
            imagen_principal = imagenes_base64[0] if imagenes_base64 else ""

            # Guardar en BD (ahora con nombres)
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
                aprovechamiento_total=aprovechamiento
            )

            # Guardar la primera imagen en el FileField
            if imagen_principal:
                image_data = base64.b64decode(imagen_principal)
                file = ContentFile(image_data, name=f"optimizacion_{request.user.username}_{optimizacion.id}.png")
                optimizacion.imagen.save(f"optimizacion_{request.user.username}_{optimizacion.id}.png", file)
            
            # Calcular el número de lista para el PDF (basado en orden por fecha descendente por defecto)
            # Obtener todas las optimizaciones ordenadas por fecha descendente (igual que en mis_optimizaciones)
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
            
            messages.success(request, f"✅ Optimización creada exitosamente. Aprovechamiento: {aprovechamiento:.2f}%")
            
            # Obtener unidad de la optimización
            unidad = getattr(optimizacion, 'unidad_medida', 'cm') or 'cm'
            
            # Convertir áreas de cm² a la unidad del usuario para mostrar
            # Para áreas: si 1 cm = X unidades, entonces 1 cm² = X² unidades²
            from .utils import convertir_desde_cm, obtener_simbolo_area
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
            })
        else:
            # Mostrar errores de validación
            if not tablero_form.is_valid():
                messages.error(request, "❌ Error en las dimensiones del tablero.")
            if not pieza_formset.is_valid():
                messages.error(request, "❌ Error en los datos de las piezas.")

    else:
        tablero_form = TableroForm()
        pieza_formset = PiezaFormSet()

    return render(request, "opticut/index.html", {
        "tablero_form": tablero_form,
        "pieza_formset": pieza_formset
    })


@login_required
def mis_optimizaciones(request):
    optimizaciones = Optimizacion.objects.filter(usuario=request.user)
    
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
    
    # Ordenamiento
    ordenar_por = request.GET.get('ordenar_por', 'fecha_desc')
    
    if ordenar_por == 'fecha_desc':
        optimizaciones = optimizaciones.order_by('-fecha')
    elif ordenar_por == 'fecha_asc':
        optimizaciones = optimizaciones.order_by('fecha')
    elif ordenar_por == 'aprovechamiento_desc':
        optimizaciones = optimizaciones.order_by('-aprovechamiento_total')
    elif ordenar_por == 'aprovechamiento_asc':
        optimizaciones = optimizaciones.order_by('aprovechamiento_total')
    else:
        # Por defecto: fecha descendente
        optimizaciones = optimizaciones.order_by('-fecha')
    
    total_optimizaciones = optimizaciones.count()
    
    # Determinar si el ordenamiento es descendente o ascendente
    es_descendente = ordenar_por in ['fecha_desc', 'aprovechamiento_desc']
    
    # Procesar piezas para cada optimización
    optimizaciones_con_piezas = []
    for idx, opt in enumerate(optimizaciones, start=1):
        # Calcular número de lista según el ordenamiento
        if es_descendente:
            # Para orden descendente: primera = número más alto
            numero_mostrado = total_optimizaciones - idx + 1
        else:
            # Para orden ascendente: primera = número 1
            numero_mostrado = idx
        piezas_procesadas = []
        for linea in opt.piezas.splitlines():
            if linea.strip():
                partes = linea.split(',')
                if len(partes) == 4:  # Formato: nombre,ancho,alto,cantidad
                    piezas_procesadas.append({
                        'nombre': partes[0].strip(),
                        'ancho': partes[1].strip(),
                        'alto': partes[2].strip(),
                        'cantidad': partes[3].strip()
                    })
                elif len(partes) == 3:  # Formato antiguo: ancho,alto,cantidad
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
        
        optimizaciones_con_piezas.append({
            'optimizacion': opt,
            'piezas': piezas_procesadas,
            'numero': numero_mostrado,
            'ancho_mostrar': ancho_mostrar,
            'alto_mostrar': alto_mostrar,
            'unidad_medida': unidad_opt,
        })
    
    return render(request, 'opticut/mis_optimizaciones.html', {
        'optimizaciones_con_piezas': optimizaciones_con_piezas,
        'nombre_pieza': nombre_pieza,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'ordenar_por': ordenar_por,
        'solo_favoritos': solo_favoritos,
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
        
        # Obtener el ordenamiento actual desde los parámetros GET (si existe)
        ordenar_por = request.GET.get('ordenar_por', 'fecha_desc')
        
        # Aplicar el mismo ordenamiento que se usa en mis_optimizaciones
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
        for linea in optimizacion.piezas.splitlines():
            partes = linea.split(",")
            if len(partes) == 4:  # Con nombre
                nombre, w, h, c = partes
                # Convertir de unidad original a cm
                w_cm = convertir_a_cm(float(w), unidad_opt)
                h_cm = convertir_a_cm(float(h), unidad_opt)
                piezas.append((w_cm, h_cm, int(c)))
            else:  # Sin nombre (formato antiguo)
                w, h, c = partes
                # Convertir de unidad original a cm
                w_cm = convertir_a_cm(float(w), unidad_opt)
                h_cm = convertir_a_cm(float(h), unidad_opt)
                piezas.append((w_cm, h_cm, int(c)))
        
        # Generar TODAS las imágenes nuevamente (con info de desperdicio)
        # Nota: ancho_tablero y alto_tablero ya están en cm en la BD
        imagenes_base64, _, info_desperdicio = generar_grafico(piezas, optimizacion.ancho_tablero, optimizacion.alto_tablero, unidad_opt)
        
        # Generar UN SOLO PDF con todas las imágenes (usando número de lista)
        pdf_path = generar_pdf(optimizacion, imagenes_base64, numero_lista=numero_lista)
        
        full_path = os.path.join(settings.MEDIA_ROOT, pdf_path)
        return FileResponse(open(full_path, "rb"), as_attachment=True, filename=os.path.basename(full_path))
    except Exception as e:
        messages.error(request, f"Error generando PDF: {e}")
        return redirect('opticut:mis_optimizaciones')


@login_required
def resultado_view(request):
    if request.method == "POST":
        ancho = float(request.POST.get("ancho_tablero"))
        alto = float(request.POST.get("alto_tablero"))
        piezas_texto = request.POST.get("piezas")

        piezas = []
        for linea in piezas_texto.strip().splitlines():
            partes = linea.split(",")
            if len(partes) == 4:  # Con nombre
                nombre, w, h, c = partes
                piezas.append((float(w), float(h), int(c)))
            else:  # Sin nombre
                w, h, c = partes
                piezas.append((float(w), float(h), int(c)))

        # Obtener unidad (asumir cm para datos antiguos o del POST)
        unidad_resultado = request.POST.get('unidad_medida', 'cm')
        if not unidad_resultado:
            unidad_resultado = 'cm'
        
        # Generar TODAS las imágenes con info de desperdicio
        imagenes_base64, aprovechamiento, info_desperdicio = generar_grafico(piezas, ancho, alto, unidad_resultado)
        imagen_principal = imagenes_base64[0] if imagenes_base64 else ""

        optimizacion = Optimizacion.objects.create(
            usuario=request.user,
            ancho_tablero=ancho,
            alto_tablero=alto,
            unidad_medida=unidad_resultado,
            piezas=piezas_texto,
            aprovechamiento_total=aprovechamiento
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

        # Obtener unidad de la optimización
        unidad = getattr(optimizacion, 'unidad_medida', 'cm') or 'cm'
        
        # Convertir áreas de cm² a la unidad del usuario para mostrar
        from .utils import convertir_desde_cm, obtener_simbolo_area
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
        
        return render(request, "opticut/resultado.html", {
            "optimizacion": optimizacion,
            "imagen": imagen_principal,
            "imagenes": imagenes_base64,
            "pdf_path": pdf_path,
            "num_tableros": len(imagenes_base64),
            "info_desperdicio": info_desperdicio_mostrar,
            "tableros_con_imagenes": tableros_con_imagenes,
            "numero_lista": numero_lista,  # Pasar número de lista para usar en descarga PNG
            "unidad_medida": unidad,
            "simbolo_area": simbolo_area,
        })


@login_required
def duplicar_optimizacion(request, pk):
    """
    Duplica una optimización existente y carga sus datos en el formulario.
    """
    try:
        optimizacion = Optimizacion.objects.get(pk=pk, usuario=request.user)
        
        # Obtener el ordenamiento actual desde los parámetros GET (si existe)
        ordenar_por = request.GET.get('ordenar_por', 'fecha_desc')
        
        # Calcular el número de visualización igual que en mis_optimizaciones
        todas_optimizaciones = Optimizacion.objects.filter(usuario=request.user)
        
        # Aplicar filtros si existen (para mantener consistencia)
        solo_favoritos = request.GET.get('solo_favoritos', '').strip()
        if solo_favoritos == 'true':
            todas_optimizaciones = todas_optimizaciones.filter(favorito=True)
        
        nombre_pieza = request.GET.get('nombre_pieza', '').strip()
        if nombre_pieza:
            todas_optimizaciones = todas_optimizaciones.filter(piezas__icontains=nombre_pieza)
        
        # Aplicar el mismo ordenamiento que se usa en mis_optimizaciones
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
                # Calcular número de lista según el ordenamiento (igual que en mis_optimizaciones)
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
        
        # Usar el número de visualización calculado (igual que se muestra en mis_optimizaciones)
        # Esto asegura que el mensaje muestre el mismo número que se ve en la pantalla
        messages.info(request, f"📋 Cargando datos de la optimización #{numero_mostrado}. Puedes modificarlos antes de calcular.")
        
        return render(request, "opticut/index.html", {
            "tablero_form": tablero_form,
            "pieza_formset": pieza_formset,
            "duplicando": True,
            "optimizacion_original": optimizacion
        })
        
    except Optimizacion.DoesNotExist:
        messages.error(request, "No se encontró la optimización.")
        return redirect('opticut:mis_optimizaciones')


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
    })


@login_required
def toggle_favorito(request, pk):
    """
    Marca o desmarca una optimización como favorita.
    Soporta tanto peticiones AJAX como peticiones normales.
    """
    try:
        optimizacion = Optimizacion.objects.get(pk=pk, usuario=request.user)
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
    except Optimizacion.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax') == 'true':
            from django.http import JsonResponse
            return JsonResponse({
                'success': False,
                'message': 'No se encontró la optimización o no tienes permiso.'
            }, status=404)
        messages.error(request, "No se encontró la optimización o no tienes permiso.")
    
    # Redirigir de vuelta a mis_optimizaciones, manteniendo los filtros (solo si no es AJAX)
    return redirect(request.META.get('HTTP_REFERER', 'opticut:mis_optimizaciones'))


@login_required
def calcular_tiempo_corte(request, pk):
    """
    Calcula el tiempo estimado de corte para una optimización.
    Considera: número de piezas, tipo de corte, material, etc.
    """
    try:
        optimizacion = Optimizacion.objects.get(pk=pk, usuario=request.user)
        
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
        
    except Optimizacion.DoesNotExist:
        messages.error(request, "No se encontró la optimización o no tienes permiso.")
        return redirect('opticut:mis_optimizaciones')
    except Exception as e:
        messages.error(request, f"Error al calcular tiempo: {str(e)}")
        return redirect('opticut:mis_optimizaciones')


@login_required
def descargar_png(request, pk, tablero_num=None):
    """
    Descarga una imagen PNG de un tablero específico de una optimización.
    Si tablero_num no se especifica, descarga la primera imagen (tablero 1).
    """
    try:
        optimizacion = Optimizacion.objects.get(pk=pk, usuario=request.user)
        
        # Obtener el ordenamiento actual desde los parámetros GET (si existe)
        ordenar_por = request.GET.get('ordenar_por', 'fecha_desc')
        
        # Aplicar el mismo ordenamiento que se usa en mis_optimizaciones
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
        for linea in optimizacion.piezas.splitlines():
            if linea.strip():
                partes = linea.split(",")
                if len(partes) == 4:  # Con nombre
                    nombre, w, h, c = partes
                    w_cm = convertir_a_cm(float(w), unidad_opt)
                    h_cm = convertir_a_cm(float(h), unidad_opt)
                    piezas.append((w_cm, h_cm, int(c)))
                elif len(partes) == 3:  # Sin nombre
                    w, h, c = partes
                    w_cm = convertir_a_cm(float(w), unidad_opt)
                    h_cm = convertir_a_cm(float(h), unidad_opt)
                    piezas.append((w_cm, h_cm, int(c)))
        
        # Generar todas las imágenes
        imagenes_base64, _, _ = generar_grafico(piezas, optimizacion.ancho_tablero, optimizacion.alto_tablero, unidad_opt)
        
        if not imagenes_base64:
            messages.error(request, "No se encontraron imágenes para esta optimización.")
            return redirect('opticut:mis_optimizaciones')
        
        # Determinar qué tablero descargar
        if tablero_num is None:
            tablero_num = 1
        
        # Validar que el número de tablero existe
        if tablero_num < 1 or tablero_num > len(imagenes_base64):
            messages.error(request, f"El tablero #{tablero_num} no existe. Esta optimización tiene {len(imagenes_base64)} tablero(s).")
            return redirect('opticut:mis_optimizaciones')
        
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
        
    except Optimizacion.DoesNotExist:
        messages.error(request, "No se encontró la optimización o no tienes permiso.")
        return redirect('opticut:mis_optimizaciones')
    except Exception as e:
        messages.error(request, f"Error al generar imagen PNG: {str(e)}")
        return redirect('opticut:mis_optimizaciones')