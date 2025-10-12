import matplotlib.pyplot as plt
import math
import io
import base64

def colocar_piezas_multi(piezas, ancho, alto):
    tableros = []
    x, y = 0, 0
    fila_alto = 0
    posiciones = []

    for pieza_ancho, pieza_alto, cantidad in piezas:
        for _ in range(cantidad):
            if x + pieza_ancho > ancho:
                x = 0
                y += fila_alto
                fila_alto = 0
            if y + pieza_alto > alto:
                tableros.append(posiciones)
                posiciones = []
                x, y, fila_alto = 0, 0, 0
            posiciones.append((x, y, pieza_ancho, pieza_alto))
            x += pieza_ancho
            fila_alto = max(fila_alto, pieza_alto)
    if posiciones:
        tableros.append(posiciones)
    return tableros


def generar_grafico(piezas, ancho, alto):
    tableros = colocar_piezas_multi(piezas, ancho, alto)
    AREA_TABLERO = ancho * alto
    n = len(tableros)
    cols = 2
    rows = math.ceil(n / cols)

    fig, axs = plt.subplots(rows, cols, figsize=(12, 6*rows))
    if rows == 1 and cols == 1:
        axs = [[axs]]
    elif rows == 1:
        axs = [axs]
    elif cols == 1:
        axs = [[ax] for ax in axs]

    for i, posiciones in enumerate(tableros, start=1):
        r, c = divmod(i-1, cols)
        ax = axs[r][c]
        ax.set_xlim(0, ancho)
        ax.set_ylim(0, alto)
        ax.set_aspect('equal')
        area_usada = sum(w * h for (_, _, w, h) in posiciones)
        aprovechamiento = (area_usada / AREA_TABLERO) * 100
        desperdicio = 100 - aprovechamiento
        ax.set_title(f"Tablero {i}\nAprovechamiento: {aprovechamiento:.2f}% | Desperdicio: {desperdicio:.2f}%")
        for (x, y, w, h) in posiciones:
            rect = plt.Rectangle((x, y), w, h, edgecolor='blue', facecolor='lightblue')
            ax.add_patch(rect)
            ax.text(x + w/2, y + h/2, f"{w}x{h}", ha="center", va="center", fontsize=8)
    for j in range(n, rows*cols):
        r, c = divmod(j, cols)
        axs[r][c].axis("off")

    plt.tight_layout()

    # guardar imagen en base64
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode("utf-8")
    return image_base64
