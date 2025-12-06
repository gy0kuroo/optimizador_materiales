import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.dates as mdates
import io, base64
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from django.conf import settings
import os
from PIL import Image


# ===== FUNCIONES DE CONVERSIÓN DE UNIDADES =====
# Todas las conversiones son a centímetros (unidad base)

def convertir_a_cm(valor, unidad):
    """
    Convierte un valor de cualquier unidad a centímetros.
    
    Args:
        valor: Valor numérico a convertir
        unidad: Unidad de origen ('cm', 'm', 'in', 'ft')
    
    Returns:
        Valor convertido a centímetros
    """
    conversiones = {
        'cm': 1.0,           # 1 cm = 1 cm
        'm': 100.0,          # 1 m = 100 cm
        'in': 2.54,          # 1 pulgada = 2.54 cm
        'ft': 30.48,         # 1 pie = 30.48 cm
    }
    factor = conversiones.get(unidad, 1.0)
    return round(valor * factor, 2)


def convertir_desde_cm(valor_cm, unidad_destino):
    """
    Convierte un valor en centímetros a otra unidad.
    
    Args:
        valor_cm: Valor en centímetros
        unidad_destino: Unidad de destino ('cm', 'm', 'in', 'ft')
    
    Returns:
        Valor convertido a la unidad destino
    """
    conversiones = {
        'cm': 1.0,           # 1 cm = 1 cm
        'm': 0.01,           # 1 cm = 0.01 m
        'in': 1/2.54,        # 1 cm = 1/2.54 pulgadas
        'ft': 1/30.48,       # 1 cm = 1/30.48 pies
    }
    factor = conversiones.get(unidad_destino, 1.0)
    return round(valor_cm * factor, 2)


def obtener_simbolo_unidad(unidad):
    """
    Retorna el símbolo de la unidad para mostrar.
    """
    simbolos = {
        'cm': 'cm',
        'm': 'm',
        'in': 'in',
        'ft': 'ft',
    }
    return simbolos.get(unidad, 'cm')


def obtener_simbolo_area(unidad):
    """
    Retorna el símbolo de unidad al cuadrado para áreas.
    """
    simbolos = {
        'cm': 'cm²',
        'm': 'm²',
        'in': 'in²',
        'ft': 'ft²',
    }
    return simbolos.get(unidad, 'cm²')


def generar_grafico(piezas, ancho_tablero, alto_tablero, unidad='cm'):
    """
    Algoritmo First Fit Decreasing (FFD) mejorado para optimización de cortes.
    Ahora también calcula desperdicio por tablero.
    """
    AREA_TABLERO = ancho_tablero * alto_tablero
    tableros = []
    area_usada_total = 0

    # Paso 1: Expandir piezas y ordenarlas (FFD)
    piezas_expandidas = []
    for w, h, c in piezas:
        for _ in range(c):
            area = w * h
            piezas_expandidas.append({
                'ancho': w,
                'alto': h,
                'area': area,
                'original': (w, h)
            })
    
    piezas_expandidas.sort(key=lambda x: x['area'], reverse=True)
    
    # Paso 2: Algoritmo de empaquetado por niveles
    for pieza in piezas_expandidas:
        w = pieza['ancho']
        h = pieza['alto']
        colocada = False
        
        for tablero_idx, tablero in enumerate(tableros):
            posiciones = tablero['posiciones']
            niveles = tablero['niveles']
            
            for nivel in niveles:
                x = nivel['x_actual']
                y = nivel['y_inicio']
                altura_nivel = nivel['altura']
                
                if x + w <= ancho_tablero and h <= altura_nivel:
                    posiciones.append((x, y, w, h))
                    nivel['x_actual'] += w
                    area_usada_total += w * h
                    colocada = True
                    break
            
            if colocada:
                break
            
            if not colocada and niveles:
                ultimo_nivel = niveles[-1]
                y_nuevo_nivel = ultimo_nivel['y_inicio'] + ultimo_nivel['altura']
                
                if y_nuevo_nivel + h <= alto_tablero:
                    niveles.append({
                        'y_inicio': y_nuevo_nivel,
                        'x_actual': w,
                        'altura': h
                    })
                    posiciones.append((0, y_nuevo_nivel, w, h))
                    area_usada_total += w * h
                    colocada = True
                    break
        
        if not colocada:
            nuevo_tablero = {
                'posiciones': [(0, 0, w, h)],
                'niveles': [{
                    'y_inicio': 0,
                    'x_actual': w,
                    'altura': h
                }]
            }
            tableros.append(nuevo_tablero)
            area_usada_total += w * h
    
    # Paso 3: Calcular aprovechamiento y desperdicio
    num_tableros = len(tableros)
    if num_tableros == 0:
        aprovechamiento_total = 0
        desperdicio_total = 0
        info_tableros = []
    else:
        area_total_disponible = num_tableros * AREA_TABLERO
        desperdicio_total = area_total_disponible - area_usada_total
        aprovechamiento_total = round((area_usada_total / area_total_disponible) * 100, 2)
        
        # Calcular desperdicio por tablero
        info_tableros = []
        for idx, tablero in enumerate(tableros, start=1):
            area_usada_tablero = sum(w * h for _, _, w, h in tablero['posiciones'])
            desperdicio_tablero = AREA_TABLERO - area_usada_tablero
            porcentaje_uso = round((area_usada_tablero / AREA_TABLERO) * 100, 2)
            
            info_tableros.append({
                'numero': idx,
                'area_usada': area_usada_tablero,
                'desperdicio': desperdicio_tablero,
                'porcentaje_uso': porcentaje_uso,
                'num_piezas': len(tablero['posiciones'])
            })
    
    # Paso 4: Generar imágenes
    imagenes_base64 = []
    colores = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2']
    
    for i, tablero in enumerate(tableros, start=1):
        posiciones = tablero['posiciones']
        info = info_tableros[i-1]
        
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.set_xlim(0, ancho_tablero)
        ax.set_ylim(0, alto_tablero)
        ax.invert_yaxis()
        ax.set_aspect('equal')
        
        # Convertir desperdicio para mostrar
        simbolo = obtener_simbolo_unidad(unidad)
        simbolo_area = obtener_simbolo_area(unidad)
        factor_lineal = convertir_desde_cm(1, unidad)
        factor_area = factor_lineal ** 2
        desperdicio_mostrar = round(info['desperdicio'] * factor_area, 2)
        
        # Título con información de desperdicio
        ax.set_title(f"Tablero {i} de {num_tableros} - FFD\n"
                    f"Uso: {info['porcentaje_uso']}% | Desperdicio: {desperdicio_mostrar} {simbolo_area}",
                    fontsize=13, fontweight='bold', pad=20)
        ax.set_xlabel(f"Ancho ({simbolo})", fontsize=11)
        ax.set_ylabel(f"Alto ({simbolo})", fontsize=11)
        
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax.set_axisbelow(True)
        
        # Borde del tablero
        borde = patches.Rectangle((0, 0), ancho_tablero, alto_tablero,
                                  linewidth=3, edgecolor='black', 
                                  facecolor='#f0f0f0', alpha=0.3)
        ax.add_patch(borde)
        
        # Dibujar piezas
        for idx, (x, y, w, h) in enumerate(posiciones):
            color = colores[idx % len(colores)]
            
            rect = patches.Rectangle((x, y), w, h, linewidth=2,
                                     edgecolor='darkblue', facecolor=color, alpha=0.7)
            ax.add_patch(rect)
            
            # Convertir dimensiones de pieza para mostrar
            w_mostrar = round(convertir_desde_cm(w, unidad), 1)
            h_mostrar = round(convertir_desde_cm(h, unidad), 1)
            
            ax.text(x + w/2, y + h/2, f'{w_mostrar}×{h_mostrar}',
                   ha='center', va='center', fontsize=10, 
                   fontweight='bold', color='white',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7))
        
        # Información detallada (convertir áreas)
        area_usada_mostrar = round(info['area_usada'] * factor_area, 2)
        info_text = (f"Piezas: {info['num_piezas']}\n"
                    f"Área usada: {area_usada_mostrar} {simbolo_area}\n"
                    f"Desperdicio: {desperdicio_mostrar} {simbolo_area}")
        ax.text(ancho_tablero * 0.02, alto_tablero * 0.98, info_text,
               fontsize=9, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))
        
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=120, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        buf.seek(0)
        imagenes_base64.append(base64.b64encode(buf.read()).decode("utf-8"))
    
    # Retornar también información de desperdicio
    return imagenes_base64, aprovechamiento_total, {
        'area_usada_total': area_usada_total,
        'desperdicio_total': desperdicio_total,
        'info_tableros': info_tableros,
        'num_tableros': num_tableros,
        'area_total_disponible': num_tableros * AREA_TABLERO if num_tableros > 0 else 0
    }

def generar_pdf(optimizacion, imagenes_base64, numero_lista=None):
    """
    Genera UN SOLO PDF con todos los tableros, cada uno en su propia página.
    
    Args:
        optimizacion: Objeto Optimizacion
        imagenes_base64: Lista de imágenes en base64
        numero_lista: Número de la lista en el historial (opcional). Si se proporciona,
                     se usará en el nombre del archivo en lugar del ID.
    """
    if isinstance(imagenes_base64, str):
        imagenes_base64 = [imagenes_base64] if imagenes_base64 else []
    
    if not imagenes_base64:
        return None
    
    # Usar número de lista si está disponible, sino usar el ID
    if numero_lista is not None:
        filename = f"optimizacion_{optimizacion.usuario.username}_{numero_lista}.pdf"
    else:
        filename = f"optimizacion_{optimizacion.usuario.username}_{optimizacion.id}.pdf"
    filepath = os.path.join(settings.MEDIA_ROOT, "pdfs", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4

    # === PÁGINA 1: Información general ===
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 50, "Reporte de Optimización - OptiCut")
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

    # Encabezado de lista de piezas
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, height - 225, "Piezas utilizadas:")
    c.setFont("Helvetica", 10)

    y_pos = height - 245
    for linea in optimizacion.piezas.splitlines():
        if y_pos < 100:
            c.showPage()
            y_pos = height - 50
        
        try:
            partes = linea.split(',')
            if len(partes) == 4:
                nombre, ancho, alto, cantidad = partes
                texto = f"   • {cantidad}× {nombre.strip()} ({ancho.strip()} × {alto.strip()} cm)"
            else:
                ancho, alto, cantidad = partes
                texto = f"   • {cantidad.strip()}× Pieza ({ancho.strip()} × {alto.strip()} cm)"
            c.drawString(2.5*cm, y_pos, texto)
        except:
            c.drawString(2.5*cm, y_pos, f"   • {linea}")
        
        y_pos -= 18

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
    c.drawCentredString(width / 2, 0.7*cm, "OptiCut - Optimización de Recursos en Carpintería | Algoritmo FFD")
    
    c.save()
    
    return os.path.join("pdfs", filename)


def generar_grafico_aprovechamiento(optimizaciones, periodo='todos', alta_resolucion=False):
    """
    Genera un gráfico de línea mostrando la tendencia de aprovechamiento.
    
    Args:
        optimizaciones: QuerySet de optimizaciones ordenadas por fecha
        periodo: 'semanal', 'mensual', 'anual', 'todos'
        alta_resolucion: Si es True, genera una versión en alta resolución para zoom
    
    Returns:
        String base64 de la imagen del gráfico
    """
    if not optimizaciones.exists():
        return None
    
    # Ajustar tamaño y DPI según resolución
    if alta_resolucion:
        fig, ax = plt.subplots(figsize=(16, 9))
        dpi = 200
        fontsize_title = 18
        fontsize_labels = 14
        fontsize_legend = 12
        linewidth = 3
        markersize = 8
    else:
        fig, ax = plt.subplots(figsize=(12, 6))
        dpi = 100
        fontsize_title = 14
        fontsize_labels = 11
        fontsize_legend = 10
        linewidth = 2
        markersize = 6
    
    # Preparar datos
    fechas = [opt.fecha for opt in optimizaciones]
    aprovechamientos = [opt.aprovechamiento_total for opt in optimizaciones]
    
    # Calcular promedio
    promedio = sum(aprovechamientos) / len(aprovechamientos) if aprovechamientos else 0
    
    # Gráfico de línea
    ax.plot(fechas, aprovechamientos, marker='o', linewidth=linewidth, markersize=markersize, 
            color='#4ECDC4', label='Aprovechamiento')
    
    # Línea de promedio
    ax.axhline(y=promedio, color='#FF6B6B', linestyle='--', linewidth=linewidth, 
               label=f'Promedio: {promedio:.2f}%')
    
    # Formatear fechas según período
    if periodo == 'semanal':
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    elif periodo == 'mensual':
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%Y'))
    elif periodo == 'anual':
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    else:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
    
    plt.xticks(rotation=45, ha='right')
    ax.set_xlabel('Fecha', fontsize=fontsize_labels, fontweight='bold')
    ax.set_ylabel('Aprovechamiento (%)', fontsize=fontsize_labels, fontweight='bold')
    ax.set_title('📊 Tendencia de Aprovechamiento', fontsize=fontsize_title, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='best', fontsize=fontsize_legend)
    ax.set_ylim(0, 100)
    
    plt.tight_layout()
    
    # Convertir a base64
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


def generar_grafico_desperdicio(optimizaciones, periodo='todos', alta_resolucion=False):
    """
    Genera un gráfico de línea mostrando la tendencia de desperdicio.
    Calcula el desperdicio basado en el aprovechamiento.
    
    Args:
        optimizaciones: QuerySet de optimizaciones ordenadas por fecha
        periodo: 'semanal', 'mensual', 'anual', 'todos'
        alta_resolucion: Si es True, genera una versión en alta resolución para zoom
    
    Returns:
        String base64 de la imagen del gráfico
    """
    if not optimizaciones.exists():
        return None
    
    # Ajustar tamaño y DPI según resolución
    if alta_resolucion:
        fig, ax = plt.subplots(figsize=(16, 9))
        dpi = 200
        fontsize_title = 18
        fontsize_labels = 14
        fontsize_legend = 12
        linewidth = 3
        markersize = 8
    else:
        fig, ax = plt.subplots(figsize=(12, 6))
        dpi = 100
        fontsize_title = 14
        fontsize_labels = 11
        fontsize_legend = 10
        linewidth = 2
        markersize = 6
    
    # Preparar datos
    fechas = [opt.fecha for opt in optimizaciones]
    # Calcular desperdicio: 100 - aprovechamiento
    desperdicios = [100 - opt.aprovechamiento_total for opt in optimizaciones]
    
    # Calcular promedio
    promedio = sum(desperdicios) / len(desperdicios) if desperdicios else 0
    
    # Gráfico de línea
    ax.plot(fechas, desperdicios, marker='s', linewidth=linewidth, markersize=markersize, 
            color='#FF6B6B', label='Desperdicio')
    
    # Línea de promedio
    ax.axhline(y=promedio, color='#4ECDC4', linestyle='--', linewidth=linewidth, 
               label=f'Promedio: {promedio:.2f}%')
    
    # Formatear fechas según período
    if periodo == 'semanal':
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    elif periodo == 'mensual':
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%Y'))
    elif periodo == 'anual':
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    else:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
    
    plt.xticks(rotation=45, ha='right')
    ax.set_xlabel('Fecha', fontsize=fontsize_labels, fontweight='bold')
    ax.set_ylabel('Desperdicio (%)', fontsize=fontsize_labels, fontweight='bold')
    ax.set_title('📉 Tendencia de Desperdicio', fontsize=fontsize_title, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='best', fontsize=fontsize_legend)
    ax.set_ylim(0, 100)
    
    plt.tight_layout()
    
    # Convertir a base64
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')