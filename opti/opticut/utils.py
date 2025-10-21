import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io, base64

def generar_grafico(piezas, ancho_tablero, alto_tablero):
    """
    Genera uno o más tableros según las piezas ingresadas.
    Devuelve una imagen combinada y el aprovechamiento total.
    """
    AREA_TABLERO = ancho_tablero * alto_tablero
    tableros = []
    actual = []
    x, y, max_row_height = 0, 0, 0
    area_usada = 0

    # Copia las piezas como lista expandida (cada pieza repetida según cantidad)
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

    aprovechamiento_total = round((area_usada / (len(tableros) * AREA_TABLERO)) * 100, 2)

    # Crear figura combinada
    filas = len(tableros)
    fig, axes = plt.subplots(filas, 1, figsize=(6, 6 * filas))
    if filas == 1:
        axes = [axes]

    for i, (ax, posiciones) in enumerate(zip(axes, tableros), start=1):
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
    image_base64 = base64.b64encode(buf.read()).decode("utf-8")

    return image_base64, aprovechamiento_total
