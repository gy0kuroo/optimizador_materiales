"""Generacion de reportes PDF."""
import base64
import io
import os

from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from django.conf import settings

from ..packing import normalizar_info_desperdicio
from ..render import _info_desperdicio_desde_optimizacion
from ..units import convertir_a_cm, convertir_desde_cm, obtener_simbolo_area, obtener_simbolo_unidad

def generar_pdf(optimizacion, imagenes_base64, numero_lista=None, info_desperdicio=None):
    """
    Genera UN SOLO PDF con todos los tableros, cada uno en su propia página.
    
    Args:
        optimizacion: Objeto Optimizacion
        imagenes_base64: Lista de imágenes en base64
        numero_lista: Número de la lista en el historial (opcional). Si se proporciona,
                     se usará en el nombre del archivo en lugar del ID.
        info_desperdicio: Dict igual al tercer retorno de generar_grafico (areas en cm²).
                         Si es None, se regenera desde la optimización guardada (más costoso).
    """
    if isinstance(imagenes_base64, str):
        imagenes_base64 = [imagenes_base64] if imagenes_base64 else []
    
    if not imagenes_base64:
        return None
    
    numero = numero_lista if numero_lista is not None else optimizacion.id
    filename = f"optimizacion_{numero}.pdf"
    filepath = os.path.join(settings.MEDIA_ROOT, "pdfs", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4

    # === PÁGINA 1: Información general ===
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 50, "Reporte de Optimización - CutLess")
    c.setFont("Helvetica-Oblique", 10)
    c.drawCentredString(width / 2, height - 70, "Algoritmo: First Fit Decreasing (FFD)")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, height - 110, "Información General:")
    c.setFont("Helvetica", 11)
    c.drawString(2.5*cm, height - 130, f"• Usuario: {optimizacion.usuario.username}")
    c.drawString(2.5*cm, height - 145, f"• Fecha: {optimizacion.fecha.strftime('%d/%m/%Y %H:%M')}")
    # Obtener unidad y convertir dimensiones para mostrar
    unidad = getattr(optimizacion, 'unidad_medida', 'cm') or 'cm'
    ancho_mostrar = convertir_desde_cm(optimizacion.ancho_tablero, unidad)
    alto_mostrar = convertir_desde_cm(optimizacion.alto_tablero, unidad)
    simbolo = obtener_simbolo_unidad(unidad)
    
    c.drawString(2.5*cm, height - 160, f"• Dimensiones del tablero: {ancho_mostrar} × {alto_mostrar} {simbolo}")
    c.drawString(2.5*cm, height - 175, f"• Tableros generados: {len(imagenes_base64)}")
    
    c.setFont("Helvetica-Bold", 12)
    c.setFillColorRGB(0, 0.5, 0)
    c.drawString(2.5*cm, height - 195, f"• Aprovechamiento: {optimizacion.aprovechamiento_total:.2f}%")
    c.setFillColorRGB(0, 0, 0)
    
    # Información de costos (si existe)
    costo_total = optimizacion.get_costo_total()
    if costo_total or optimizacion.precio_tablero or optimizacion.mano_obra:
        y_pos_costo = height - 220
        c.setFont("Helvetica-Bold", 12)
        c.setFillColorRGB(0, 0.5, 0.8)
        c.drawString(2*cm, y_pos_costo, "Información de Costos:")
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 11)
        y_pos_costo -= 20
        
        if optimizacion.material:
            c.drawString(2.5*cm, y_pos_costo, f"• Material: {optimizacion.material.nombre}")
            y_pos_costo -= 15
        
        if optimizacion.precio_tablero:
            c.drawString(2.5*cm, y_pos_costo, f"• Precio por tablero: ${optimizacion.precio_tablero:,.0f}")
            y_pos_costo -= 15
            if optimizacion.num_tableros:
                costo_material = optimizacion.precio_tablero * optimizacion.num_tableros
                c.drawString(2.5*cm, y_pos_costo, f"• Costo de material ({optimizacion.num_tableros} tableros): ${costo_material:,.0f}")
                y_pos_costo -= 15
        
        if optimizacion.mano_obra:
            c.drawString(2.5*cm, y_pos_costo, f"• Mano de obra: ${optimizacion.mano_obra:,.0f}")
            y_pos_costo -= 15
        
        if costo_total:
            c.setFont("Helvetica-Bold", 12)
            c.setFillColorRGB(0, 0.5, 0)
            c.drawString(2.5*cm, y_pos_costo, f"• COSTO TOTAL: ${costo_total:,.0f}")
            c.setFillColorRGB(0, 0, 0)
            y_pos_costo -= 20
        
        # Ajustar posición inicial de piezas
        height_piezas = y_pos_costo - 10
    else:
        height_piezas = height - 225

    # Encabezado de lista de piezas
    # Tabla de piezas detallada
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, height_piezas, "Lista de Piezas:")
    c.setFont("Helvetica-Bold", 10)
    
    # Encabezados de tabla
    y_pos = height_piezas - 20
    c.drawString(2.5*cm, y_pos, "Cant.")
    c.drawString(4*cm, y_pos, "Nombre")
    c.drawString(9*cm, y_pos, "Dimensiones")
    c.drawString(14*cm, y_pos, "Área unit.")
    c.drawString(17.5*cm, y_pos, "Área total")
    
    # Línea separadora
    y_pos -= 5
    c.line(2*cm, y_pos, width - 2*cm, y_pos)
    y_pos -= 15
    
    c.setFont("Helvetica", 9)
    total_area_piezas = 0
    total_cantidad_piezas = 0
    
    for linea in optimizacion.piezas.splitlines():
        if y_pos < 120:  # Más espacio para tabla
            c.showPage()
            y_pos = height - 50
            # Reimprimir encabezados si hay nueva página
            c.setFont("Helvetica-Bold", 10)
            c.drawString(2.5*cm, y_pos, "Cant.")
            c.drawString(4*cm, y_pos, "Nombre")
            c.drawString(9*cm, y_pos, "Dimensiones")
            c.drawString(14*cm, y_pos, "Área unit.")
            c.drawString(17.5*cm, y_pos, "Área total")
            y_pos -= 5
            c.line(2*cm, y_pos, width - 2*cm, y_pos)
            y_pos -= 15
            c.setFont("Helvetica", 9)
        
        try:
            partes = linea.split(',')
            if len(partes) == 4:
                nombre, ancho_str, alto_str, cantidad_str = partes
                nombre = nombre.strip()
                ancho = float(ancho_str.strip())
                alto = float(alto_str.strip())
                cantidad = int(cantidad_str.strip())
            else:
                ancho_str, alto_str, cantidad_str = partes
                nombre = "Pieza"
                ancho = float(ancho_str.strip())
                alto = float(alto_str.strip())
                cantidad = int(cantidad_str.strip())
            
            # Convertir a cm si es necesario
            ancho_cm = convertir_a_cm(ancho, optimizacion.unidad_medida)
            alto_cm = convertir_a_cm(alto, optimizacion.unidad_medida)
            
            # Calcular áreas
            area_unit_cm2 = ancho_cm * alto_cm
            area_total_cm2 = area_unit_cm2 * cantidad
            
            # Convertir para mostrar
            simbolo_area = obtener_simbolo_area(optimizacion.unidad_medida)
            factor_lineal = convertir_desde_cm(1, optimizacion.unidad_medida)
            factor_area = factor_lineal ** 2
            
            area_unit_mostrar = round(area_unit_cm2 * factor_area, 2)
            area_total_mostrar = round(area_total_cm2 * factor_area, 2)
            
            ancho_mostrar = round(convertir_desde_cm(ancho_cm, optimizacion.unidad_medida), 1)
            alto_mostrar = round(convertir_desde_cm(alto_cm, optimizacion.unidad_medida), 1)
            
            # Dibujar fila
            c.drawString(2.5*cm, y_pos, str(cantidad))
            c.drawString(4*cm, y_pos, nombre[:20])  # Limitar longitud
            c.drawString(9*cm, y_pos, f"{ancho_mostrar} × {alto_mostrar} {obtener_simbolo_unidad(optimizacion.unidad_medida)}")
            c.drawString(14*cm, y_pos, f"{area_unit_mostrar} {simbolo_area}")
            c.drawString(17.5*cm, y_pos, f"{area_total_mostrar} {simbolo_area}")
            
            total_area_piezas += area_total_cm2
            total_cantidad_piezas += cantidad
            
        except Exception as e:
            c.drawString(2.5*cm, y_pos, f"Error: {linea}")
        
        y_pos -= 15
    
    # Resumen de piezas
    y_pos -= 10
    c.line(2*cm, y_pos, width - 2*cm, y_pos)
    y_pos -= 15
    c.setFont("Helvetica-Bold", 10)
    simbolo_area = obtener_simbolo_area(optimizacion.unidad_medida)
    factor_lineal = convertir_desde_cm(1, optimizacion.unidad_medida)
    factor_area = factor_lineal ** 2
    total_area_mostrar = round(total_area_piezas * factor_area, 2)
    c.drawString(17.5*cm, y_pos, f"Total: {total_area_mostrar} {simbolo_area}")
    c.drawString(2.5*cm, y_pos, f"Total piezas: {total_cantidad_piezas}")
    
    # Información de configuración
    y_pos -= 30
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2*cm, y_pos, "Configuración de optimización:")
    c.setFont("Helvetica", 9)
    y_pos -= 15
    rotacion_texto = "Sí" if getattr(optimizacion, 'permitir_rotacion', True) else "No"
    c.drawString(2.5*cm, y_pos, f"• Rotación automática: {rotacion_texto}")
    y_pos -= 12
    # El margen de corte se guarda en cm, pero siempre se muestra en mm
    margen_cm = getattr(optimizacion, 'margen_corte', 0.3)
    margen_mm = round(margen_cm * 10, 1)  # Convertir de cm a mm
    c.drawString(2.5*cm, y_pos, f"• Margen de corte (kerf): {margen_mm} mm")
    
    y_pos -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y_pos, "Resumen por Tablero:")
    y_pos -= 15
    c.setFont("Helvetica-Bold", 9)
    c.drawString(2.5*cm, y_pos, "Tablero")
    c.drawString(5*cm, y_pos, "Piezas")
    c.drawString(8*cm, y_pos, "Área usada")
    c.drawString(12*cm, y_pos, "Desperdicio")
    c.drawString(16*cm, y_pos, "% Uso")
    y_pos -= 5
    c.line(2*cm, y_pos, width - 2*cm, y_pos)
    y_pos -= 12
    c.setFont("Helvetica", 9)

    if info_desperdicio is None:
        info_desperdicio = _info_desperdicio_desde_optimizacion(optimizacion) or {}
    else:
        info_desperdicio = normalizar_info_desperdicio(info_desperdicio)
    info_tableros = info_desperdicio.get('info_tableros') or []

    for i in range(len(imagenes_base64)):
        if y_pos < 100:
            c.showPage()
            y_pos = height - 50
        c.drawString(2.5*cm, y_pos, f"Tablero {i+1}")
        if i < len(info_tableros):
            row = info_tableros[i]
            n_p = row.get('num_piezas', 0)
            au = round(float(row['area_usada']) * factor_area, 2)
            dp = round(float(row['desperdicio']) * factor_area, 2)
            pct = row.get('porcentaje_uso')
            c.drawString(5*cm, y_pos, str(n_p))
            c.drawString(8*cm, y_pos, f"{au} {simbolo_area}")
            c.drawString(12*cm, y_pos, f"{dp} {simbolo_area}")
            if pct is not None:
                c.drawString(16*cm, y_pos, f"{float(pct):.2f}%")
            else:
                c.drawString(16*cm, y_pos, "-")
        else:
            for col_x in (5*cm, 8*cm, 12*cm, 16*cm):
                c.drawString(col_x, y_pos, "-")
        y_pos -= 12

    # === PÁGINAS SIGUIENTES: Un tablero por página ===
    for i, img_base64 in enumerate(imagenes_base64, start=1):
        if not img_base64 or img_base64.isspace():
            continue

        try:
            c.showPage()
            
            c.setFont("Helvetica-Bold", 16)
            c.drawCentredString(width / 2, height - 40, f"Tablero {i} de {len(imagenes_base64)}")

            image_data = base64.b64decode(img_base64)
            img_temp = os.path.join(settings.MEDIA_ROOT, f"temp_img_{optimizacion.id}_{i}.png")
            with open(img_temp, "wb") as f:
                f.write(image_data)

            with Image.open(img_temp) as im:
                img_width, img_height = im.size
                max_width = 18 * cm
                max_height = 23 * cm
                ratio = min(max_width / img_width, max_height / img_height)
                final_width = img_width * ratio
                final_height = img_height * ratio

            x_pos = (width - final_width) / 2
            y_pos = (height - final_height - 3*cm) / 2
            
            c.drawImage(img_temp, x_pos, y_pos, width=final_width, height=final_height, 
                       preserveAspectRatio=True, mask='auto')

            c.setFont("Helvetica-Oblique", 9)
            c.drawCentredString(width / 2, 1.5*cm, f"Página {i+1} de {len(imagenes_base64)+1}")

            try:
                os.remove(img_temp)
            except Exception:
                pass

        except Exception as e:
            c.setFont("Helvetica-Oblique", 10)
            c.drawString(2*cm, height / 2, f"Error: {str(e)}")

    # Pie de página final
    c.setStrokeColorRGB(0.3, 0.3, 0.3)
    c.line(2*cm, 1*cm, width - 2*cm, 1*cm)
    c.setFont("Helvetica", 8)
    c.drawCentredString(width / 2, 0.7*cm, "CutLess - Optimización de Recursos en Carpintería | Algoritmo FFD")
    
    c.save()
    
    return os.path.join("pdfs", filename)

def generar_pdf_presupuesto(presupuesto):
    """
    Genera un PDF profesional del presupuesto.
    
    Args:
        presupuesto: Objeto Presupuesto
        
    Returns:
        str: Ruta del archivo PDF generado
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from django.utils import timezone
    
    filename = f"presupuesto_{presupuesto.numero.replace('-', '_')}.pdf"
    filepath = os.path.join(settings.MEDIA_ROOT, "presupuestos", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4
    
    # === ENCABEZADO ===
    c.setFont("Helvetica-Bold", 24)
    c.setFillColorRGB(0, 0.3, 0.6)
    c.drawCentredString(width / 2, height - 50, "PRESUPUESTO")
    
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(width / 2, height - 75, f"Número: {presupuesto.numero}")
    
    # === INFORMACIÓN DEL CLIENTE ===
    y_pos = height - 120
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y_pos, "Cliente:")
    c.setFont("Helvetica", 11)
    y_pos -= 20
    
    if presupuesto.cliente:
        cliente = presupuesto.cliente
        c.drawString(2.5*cm, y_pos, f"• Nombre: {cliente.nombre}")
        y_pos -= 15
        if cliente.rut:
            c.drawString(2.5*cm, y_pos, f"• RUT: {cliente.rut}")
            y_pos -= 15
        if cliente.email:
            c.drawString(2.5*cm, y_pos, f"• Email: {cliente.email}")
            y_pos -= 15
        if cliente.telefono:
            c.drawString(2.5*cm, y_pos, f"• Teléfono: {cliente.telefono}")
            y_pos -= 15
        if cliente.direccion:
            c.drawString(2.5*cm, y_pos, f"• Dirección: {cliente.direccion}")
            y_pos -= 15
    else:
        c.drawString(2.5*cm, y_pos, "• Sin cliente asignado")
        y_pos -= 15
    
    y_pos -= 10
    
    # === INFORMACIÓN DEL PRESUPUESTO ===
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y_pos, "Información del Presupuesto:")
    c.setFont("Helvetica", 11)
    y_pos -= 20
    
    c.drawString(2.5*cm, y_pos, f"• Fecha de creación: {presupuesto.fecha_creacion.strftime('%d/%m/%Y %H:%M')}")
    y_pos -= 15
    c.drawString(2.5*cm, y_pos, f"• Válido hasta: {presupuesto.fecha_validez.strftime('%d/%m/%Y')}")
    y_pos -= 15
    c.drawString(2.5*cm, y_pos, f"• Estado: {presupuesto.get_estado_display()}")
    y_pos -= 15
    
    # === DETALLES DE LAS OPTIMIZACIONES ===
    optimizaciones = presupuesto.optimizaciones.all()
    y_pos -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y_pos, f"Detalles de las Optimizaciones ({optimizaciones.count()}):")
    c.setFont("Helvetica", 11)
    y_pos -= 20
    
    for idx, optimizacion in enumerate(optimizaciones, start=1):
        unidad = getattr(optimizacion, 'unidad_medida', 'cm') or 'cm'
        ancho_mostrar = convertir_desde_cm(optimizacion.ancho_tablero, unidad)
        alto_mostrar = convertir_desde_cm(optimizacion.alto_tablero, unidad)
        simbolo = obtener_simbolo_unidad(unidad)
        
        c.drawString(2.5*cm, y_pos, f"Optimización #{idx}:")
        y_pos -= 15
        c.drawString(3*cm, y_pos, f"• Dimensiones: {ancho_mostrar:.2f} × {alto_mostrar:.2f} {simbolo}")
        y_pos -= 15
        c.drawString(3*cm, y_pos, f"• Tableros: {optimizacion.num_tableros or 0}")
        y_pos -= 15
        c.drawString(3*cm, y_pos, f"• Aprovechamiento: {optimizacion.aprovechamiento_total:.2f}%")
        y_pos -= 15
        
        if optimizacion.material:
            c.drawString(3*cm, y_pos, f"• Material: {optimizacion.material.nombre}")
            y_pos -= 15
        
        # Agregar lista de piezas con nombres
        if optimizacion.piezas:
            c.setFont("Helvetica-Bold", 10)
            c.drawString(3*cm, y_pos, "• Piezas:")
            y_pos -= 12
            c.setFont("Helvetica", 9)
            
            # Parsear piezas
            piezas_list = []
            for linea in optimizacion.piezas.splitlines():
                if linea.strip():
                    partes = linea.split(',')
                    if len(partes) == 4:  # Formato con nombre: nombre,ancho,alto,cantidad
                        nombre = partes[0].strip()
                        ancho_pieza = float(partes[1].strip())
                        alto_pieza = float(partes[2].strip())
                        cantidad = int(partes[3].strip())
                        # Convertir dimensiones a la unidad de la optimización
                        ancho_mostrar_pieza = round(convertir_desde_cm(ancho_pieza, unidad), 2)
                        alto_mostrar_pieza = round(convertir_desde_cm(alto_pieza, unidad), 2)
                        piezas_list.append({
                            'nombre': nombre,
                            'ancho': ancho_mostrar_pieza,
                            'alto': alto_mostrar_pieza,
                            'cantidad': cantidad
                        })
                    elif len(partes) == 3:  # Formato sin nombre: ancho,alto,cantidad
                        ancho_pieza = float(partes[0].strip())
                        alto_pieza = float(partes[1].strip())
                        cantidad = int(partes[2].strip())
                        ancho_mostrar_pieza = round(convertir_desde_cm(ancho_pieza, unidad), 2)
                        alto_mostrar_pieza = round(convertir_desde_cm(alto_pieza, unidad), 2)
                        piezas_list.append({
                            'nombre': f"Pieza {len(piezas_list) + 1}",
                            'ancho': ancho_mostrar_pieza,
                            'alto': alto_mostrar_pieza,
                            'cantidad': cantidad
                        })
            
            # Mostrar piezas (máximo 5 para no ocupar mucho espacio)
            for pieza in piezas_list[:5]:
                if y_pos < 150:  # Si se acerca al final de la página, salir
                    break
                texto_pieza = f"  - {pieza['nombre']}: {pieza['ancho']:.2f} × {pieza['alto']:.2f} {simbolo} (x{pieza['cantidad']})"
                # Truncar si es muy largo
                if len(texto_pieza) > 70:
                    texto_pieza = texto_pieza[:67] + "..."
                c.drawString(3.5*cm, y_pos, texto_pieza)
                y_pos -= 11
            
            # Si hay más de 5 piezas, indicarlo
            if len(piezas_list) > 5:
                c.drawString(3.5*cm, y_pos, f"  ... y {len(piezas_list) - 5} pieza(s) más")
                y_pos -= 11
            
            c.setFont("Helvetica", 11)  # Volver al tamaño normal
        
        y_pos -= 5  # Espacio entre optimizaciones
    
    # === DESGLOSE DE COSTOS ===
    y_pos -= 20
    c.setFont("Helvetica-Bold", 12)
    c.setFillColorRGB(0, 0.5, 0.8)
    c.drawString(2*cm, y_pos, "Desglose de Costos:")
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 11)
    y_pos -= 20
    
    # Tabla de costos - considerar todas las optimizaciones
    data = [['Concepto', 'Cantidad', 'Precio Unitario', 'Subtotal']]
    
    # Calcular número de lista para cada optimización (basado en orden por fecha descendente)
    todas_optimizaciones_usuario = Optimizacion.objects.filter(usuario=presupuesto.optimizaciones.first().usuario).order_by('-fecha')
    total_optimizaciones_usuario = todas_optimizaciones_usuario.count()
    
    # Agregar fila por cada optimización
    total_tableros = 0
    for optimizacion in optimizaciones:
        num_tableros = optimizacion.num_tableros or 0
        total_tableros += num_tableros
        costo_tableros = presupuesto.precio_tablero * Decimal(str(num_tableros))
        
        # Calcular el número de lista (basado en orden por fecha descendente)
        numero_lista = optimizacion.pk  # Por defecto usar el ID
        for idx, opt in enumerate(todas_optimizaciones_usuario, start=1):
            if opt.id == optimizacion.id:
                # Para orden descendente: numero = total - idx + 1
                numero_lista = total_optimizaciones_usuario - idx + 1
                break
        
        data.append([
            f'Tableros (Optimización #{numero_lista})',
            str(num_tableros),
            f"${presupuesto.precio_tablero:,.0f}",
            f"${costo_tableros:,.0f}"
        ])
    
    # Agregar mano de obra (una sola vez, no por optimización)
    if optimizaciones.count() > 0:
        data.append([
            'Mano de Obra',
            '1',
            f"${presupuesto.mano_obra:,.0f}",
            f"${presupuesto.mano_obra:,.0f}"
        ])
    
    tabla = Table(data, colWidths=[6*cm, 3*cm, 4*cm, 4*cm])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    
    tabla.wrapOn(c, width - 4*cm, height)
    tabla.drawOn(c, 2*cm, y_pos - 80)
    
    # === TOTAL ===
    y_pos_total = y_pos - 120
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0.8, 0.2, 0)
    c.drawString(12*cm, y_pos_total, f"TOTAL: ${presupuesto.costo_total:,.0f}")
    c.setFillColorRGB(0, 0, 0)
    
    # === NOTAS ===
    if presupuesto.notas:
        y_pos_notas = y_pos_total - 40
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2*cm, y_pos_notas, "Notas:")
        c.setFont("Helvetica", 10)
        # Dividir notas en líneas
        notas_lines = presupuesto.notas.split('\n')
        y_pos_notas -= 15
        for line in notas_lines[:10]:  # Máximo 10 líneas
            if y_pos_notas < 100:
                break
            c.drawString(2.5*cm, y_pos_notas, line[:80])  # Máximo 80 caracteres por línea
            y_pos_notas -= 12
    
    # === PIE DE PÁGINA ===
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawCentredString(width / 2, 30, f"Generado el {timezone.now().strftime('%d/%m/%Y %H:%M')} - CutLess")
    
    c.save()
    return filepath

def generar_pdf_resumen_desperdicio(optimizaciones, estadisticas, periodo='todos'):
    """
    Genera un PDF con el resumen de desperdicio desde estadísticas.
    
    Args:
        optimizaciones: QuerySet de optimizaciones filtradas
        estadisticas: Diccionario con estadísticas calculadas
        periodo: Período seleccionado (todos, semanal, mensual, anual)
    
    Returns:
        str: Ruta del archivo PDF generado
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from django.utils import timezone
    import os
    from django.conf import settings
    
    filename = f"resumen_desperdicio_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(settings.MEDIA_ROOT, "pdfs", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Retornar path relativo para compatibilidad con FileResponse
    relative_path = os.path.join("pdfs", filename)
    
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4
    
    # === PÁGINA 1: RESUMEN ===
    c.setFont("Helvetica-Bold", 18)
    c.setFillColorRGB(0.86, 0.21, 0.27)  # Rojo para desperdicio
    c.drawCentredString(width / 2, height - 50, "📊 RESUMEN DE DESPERDICIO")
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(width / 2, height - 70, "Reporte de Eficiencia - CutLess")
    
    # Período
    periodo_texto = {
        'todos': 'Todos los tiempos',
        'semanal': 'Última semana',
        'mensual': 'Último mes',
        'anual': 'Último año'
    }.get(periodo, 'Todos los tiempos')
    
    c.setFont("Helvetica", 11)
    c.drawString(2*cm, height - 100, f"Período: {periodo_texto}")
    c.drawString(2*cm, height - 115, f"Fecha del reporte: {timezone.now().strftime('%d/%m/%Y %H:%M')}")
    
    # Estadísticas principales
    y_pos = height - 150
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y_pos, "Estadísticas Generales:")
    c.setFont("Helvetica", 11)
    y_pos -= 20
    
    stats = [
        f"Total Optimizaciones: {estadisticas.get('total_optimizaciones', 0)}",
        f"Aprovechamiento Promedio: {estadisticas.get('promedio_aprovechamiento', 0):.2f}%",
        f"Desperdicio Promedio: {estadisticas.get('promedio_desperdicio', 0):.2f}%",
        f"Mejor Aprovechamiento: {estadisticas.get('max_aprovechamiento', 0):.2f}%",
        f"Peor Aprovechamiento: {estadisticas.get('min_aprovechamiento', 0):.2f}%",
    ]
    
    for stat in stats:
        c.drawString(2.5*cm, y_pos, f"• {stat}")
        if 'Desperdicio' in stat:
            c.setFillColorRGB(0.86, 0.21, 0.27)
            c.drawString(2.5*cm, y_pos, f"• {stat}")
            c.setFillColorRGB(0, 0, 0)
        y_pos -= 18
    
    # === PÁGINA 2+: DETALLE ===
    c.showPage()
    
    # Encabezados de tabla
    y_pos = height - 50
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y_pos, "Detalle de Optimizaciones:")
    y_pos -= 25
    
    # Encabezados de columnas
    headers = ['Fecha', 'Dimensiones', 'Aprovech.', 'Desperd.', 'Tableros']
    x_positions = [2*cm, 5*cm, 10*cm, 13*cm, 16*cm]
    
    c.setFont("Helvetica-Bold", 9)
    for header, x_pos in zip(headers, x_positions):
        c.drawString(x_pos, y_pos, header)
    
    y_pos -= 15
    c.setFont("Helvetica", 8)
    
    # Datos
    for opt in optimizaciones.order_by('fecha')[:30]:  # Máximo 30 por página
        if y_pos < 50:
            c.showPage()
            y_pos = height - 50
        
        fecha_str = opt.fecha.strftime('%d/%m/%Y')
        unidad_opt = getattr(opt, 'unidad_medida', 'cm') or 'cm'
        ancho_mostrar = round(convertir_desde_cm(opt.ancho_tablero, unidad_opt), 2)
        alto_mostrar = round(convertir_desde_cm(opt.alto_tablero, unidad_opt), 2)
        simbolo = obtener_simbolo_unidad(unidad_opt)
        dim_str = f"{ancho_mostrar}×{alto_mostrar}{simbolo}"
        
        aprovechamiento = opt.aprovechamiento_total or 0
        desperdicio = 100 - aprovechamiento
        num_tableros = opt.num_tableros or 1
        
        c.drawString(x_positions[0], y_pos, fecha_str)
        c.drawString(x_positions[1], y_pos, dim_str)
        c.drawString(x_positions[2], y_pos, f"{aprovechamiento:.1f}%")
        
        # Colorear desperdicio
        if desperdicio > 30:
            c.setFillColorRGB(0.86, 0.21, 0.27)
        elif desperdicio > 15:
            c.setFillColorRGB(1.0, 0.76, 0.03)
        else:
            c.setFillColorRGB(0.13, 0.55, 0.13)
        c.drawString(x_positions[3], y_pos, f"{desperdicio:.1f}%")
        c.setFillColorRGB(0, 0, 0)
        
        c.drawString(x_positions[4], y_pos, str(num_tableros))
        
        y_pos -= 15
    
    # Pie de página
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawCentredString(width / 2, 30, f"Generado el {timezone.now().strftime('%d/%m/%Y %H:%M')} - CutLess")
    
    c.save()
    return relative_path