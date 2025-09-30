import matplotlib.pyplot as plt

print("🔹 OPTIMIZADOR DE CORTE PARA CARPINTERÍA 🔹")

TABLERO_ANCHO = int(input("Ingrese el ANCHO del tablero (cm): "))
TABLERO_ALTO = int(input("Ingrese el ALTO del tablero (cm): "))

num_piezas = int(input("¿Cuántos tipos de piezas quiere ingresar?: "))

piezas = []
for i in range(num_piezas):
    print(f"\nPieza {i+1}:")
    ancho = int(input("  Ancho (cm): "))
    alto = int(input("  Alto (cm): "))
    cantidad = int(input("  Cantidad: "))
    piezas.append((ancho, alto, cantidad))


def colocar_piezas_multi(piezas, ancho, alto):
    """Devuelve una lista de tableros con las posiciones de las piezas colocadas"""
    tableros = []
    x, y = 0, 0
    fila_alto = 0
    posiciones = []

    for pieza_ancho, pieza_alto, cantidad in piezas:
        for _ in range(cantidad):
            if x + pieza_ancho > ancho:  # saltar a nueva fila
                x = 0
                y += fila_alto
                fila_alto = 0

            if y + pieza_alto > alto:  # no cabe en tablero actual → guardar y abrir otro
                tableros.append(posiciones)
                posiciones = []
                x, y, fila_alto = 0, 0, 0

            posiciones.append((x, y, pieza_ancho, pieza_alto))
            x += pieza_ancho
            fila_alto = max(fila_alto, pieza_alto)

    if posiciones:  # guardar el último tablero
        tableros.append(posiciones)

    return tableros


# --- Ejecutar el algoritmo ---
tableros = colocar_piezas_multi(piezas, TABLERO_ANCHO, TABLERO_ALTO)
AREA_TABLERO = TABLERO_ANCHO * TABLERO_ALTO

# --- Dibujar cada tablero ---
for i, posiciones in enumerate(tableros, start=1):
    fig, ax = plt.subplots()
    ax.set_xlim(0, TABLERO_ANCHO)
    ax.set_ylim(0, TABLERO_ALTO)
    ax.set_aspect('equal')

    # Calcular área usada en este tablero
    area_usada = sum(w * h for (_, _, w, h) in posiciones)
    aprovechamiento = (area_usada / AREA_TABLERO) * 100
    desperdicio = 100 - aprovechamiento

    ax.set_title(f"Tablero {i} - Aprovechamiento: {aprovechamiento:.2f}% | Desperdicio: {desperdicio:.2f}%")

    # Dibujar piezas
    for (x, y, w, h) in posiciones:
        rect = plt.Rectangle((x, y), w, h, edgecolor='blue', facecolor='lightblue')
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, f"{w}x{h}", ha="center", va="center", fontsize=8)

    plt.show()
