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
    AREA_TABLERO = ancho_tablero * alto_tablero
    tableros = []
    actual = []
    x, y, max_row_height = 0, 0, 0
    area_usada = 0

    piezas_expandidas = []
    for w, h, c in piezas:
        piezas_expandidas.extend([(w, h)] * c)

    for w, h in piezas_expandidas:
        if x + w > ancho_tablero:
            x = 0
            y += max_row_height
            max_row_height = 0
        if y + h > alto_tablero:
            tableros.append(actual)
            actual = []
            x = y = max_row_height = 0
        actual.append((x, y, w, h))
        x += w
        max_row_height = max(max_row_height, h)
        area_usada += w * h

    if actual:
        tableros.append(actual)

    if len(tableros) == 0:
        aprovechamiento_total = 0
    else:
        aprovechamiento_total = round((area_usada / (len(tableros) * AREA_TABLERO)) * 100, 2)

    imagenes_base64 = []
    for i, posiciones in enumerate(tableros, start=1):
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.set_xlim(0, ancho_tablero)
        ax.set_ylim(0, alto_tablero)
        ax.invert_yaxis()
        ax.set_title(f"Tablero {i}")
        ax.set_xlabel("Ancho (cm)")
        ax.set_ylabel("Alto (cm)")

        for (x, y, w, h) in posiciones:
            rect = patches.Rectangle((x, y), w, h, linewidth=1.5,
                                     edgecolor="blue", facecolor="cyan", alpha=0.5)
            ax.add_patch(rect)

        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        plt.close(fig)
        buf.seek(0)
        imagenes_base64.append(base64.b64encode(buf.read()).decode("utf-8"))

    return imagenes_base64, aprovechamiento_total


def generar_pdf(optimizacion, imagenes_base64):
    """
    Genera un PDF con los datos de la optimización y devuelve la ruta del archivo generado.
    Ahora cada tablero se genera en un PDF separado.
    """
    # Convertir imagenes_base64 a lista si es string
    if isinstance(imagenes_base64, str):
        imagenes_base64 = [imagenes_base64] if imagenes_base64 else []
    
    # Lista para almacenar las rutas de todos los PDFs generados
    pdf_paths = []
    
    # Generar un PDF por cada tablero
    for i, img_base64 in enumerate(imagenes_base64, start=1):
        if not img_base64 or img_base64.isspace():
            continue
        
        # Nombre único para cada PDF
        filename = f"optimizacion_{optimizacion.usuario.username}_{optimizacion.id}_tablero_{i}.pdf"
        filepath = os.path.join(settings.MEDIA_ROOT, "pdfs", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        c = canvas.Canvas(filepath, pagesize=A4)
        width, height = A4

        # Título
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width / 2, height - 50, "Reporte de Optimización de Materiales - OptiCut")

        # Datos generales
        c.setFont("Helvetica", 12)
        c.drawString(2*cm, height - 100, f"Usuario: {optimizacion.usuario.username}")
        c.drawString(2*cm, height - 120, f"Fecha: {optimizacion.fecha.strftime('%d/%m/%Y %H:%M')}")
        c.drawString(2*cm, height - 140, f"Dimensiones del tablero: {optimizacion.ancho_tablero} x {optimizacion.alto_tablero} cm")
        c.drawString(2*cm, height - 160, f"Aprovechamiento total: {optimizacion.aprovechamiento_total:.2f}%")
        c.drawString(2*cm, height - 180, f"Tablero {i} de {len(imagenes_base64)}")

        # Encabezado de lista de piezas
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2*cm, height - 210, "Piezas utilizadas:")
        c.setFont("Helvetica", 11)

        y = height - 230
        for linea in optimizacion.piezas.splitlines():
            if y < 100:
                c.showPage()
                y = height - 100
            ancho, alto, cantidad = linea.split(',')
            c.drawString(3*cm, y, f"- {cantidad} piezas de {ancho} x {alto} cm")
            y -= 15

        # Insertar imagen del tablero
        try:
            image_data = base64.b64decode(img_base64)
            img_temp = os.path.join(settings.MEDIA_ROOT, f"temp_img_{optimizacion.id}_{i}.png")
            with open(img_temp, "wb") as f:
                f.write(image_data)

            with Image.open(img_temp) as im:
                img_width, img_height = im.size
                max_width = 17 * cm
                max_height = 12 * cm
                ratio = min(max_width / img_width, max_height / img_height)
                final_width = img_width * ratio
                final_height = img_height * ratio

            # Posicionar imagen en el centro
            y_pos = height / 2 - final_height / 2
            x_pos = (width - final_width) / 2
            
            c.drawImage(img_temp, x_pos, y_pos, width=final_width, height=final_height, 
                       preserveAspectRatio=True, mask='auto')

            c.setFont("Helvetica-Oblique", 10)
            c.drawCentredString(width / 2, y_pos - 20, f"Tablero {i}")

            # Eliminar imagen temporal
            try:
                os.remove(img_temp)
            except Exception:
                pass

        except Exception as e:
            c.setFont("Helvetica-Oblique", 10)
            c.drawString(2*cm, height / 2, f"Error al cargar imagen del tablero {i}: {e}")

        # Pie de página
        c.setStrokeColorRGB(0.5, 0.5, 0.5)
        c.line(2*cm, 1.5*cm, width - 2*cm, 1.5*cm)
        c.setFont("Helvetica", 9)
        c.drawCentredString(width / 2, 1.2*cm, "Generado con OptiCut - Proyecto de Optimización de Recursos en Carpintería")
        
        c.save()
        
        # Agregar la ruta relativa del PDF generado
        pdf_paths.append(os.path.join("pdfs", filename))
    
    # Retornar lista de rutas de PDFs o la primera si solo hay una
    return pdf_paths if len(pdf_paths) > 1 else (pdf_paths[0] if pdf_paths else None)