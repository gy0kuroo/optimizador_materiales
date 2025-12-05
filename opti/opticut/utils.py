import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io, base64
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from django.conf import settings
import os
from PIL import Image


def generar_grafico(piezas, ancho_tablero, alto_tablero):
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
        
        # Título con información de desperdicio
        ax.set_title(f"Tablero {i} de {num_tableros} - FFD\n"
                    f"Uso: {info['porcentaje_uso']}% | Desperdicio: {info['desperdicio']} cm²",
                    fontsize=13, fontweight='bold', pad=20)
        ax.set_xlabel("Ancho (cm)", fontsize=11)
        ax.set_ylabel("Alto (cm)", fontsize=11)
        
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
            
            ax.text(x + w/2, y + h/2, f'{w}×{h}',
                   ha='center', va='center', fontsize=10, 
                   fontweight='bold', color='white',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7))
        
        # Información detallada
        info_text = (f"Piezas: {info['num_piezas']}\n"
                    f"Área usada: {info['area_usada']} cm²\n"
                    f"Desperdicio: {info['desperdicio']} cm²")
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
    c.drawString(2.5*cm, height - 160, f"• Dimensiones del tablero: {optimizacion.ancho_tablero} × {optimizacion.alto_tablero} cm")
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