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
            # Si no cabe en la fila actual, saltar a la siguiente
            if x + pieza_ancho > ancho:
                x = 0
                y += fila_alto
                fila_alto = 0

            # Si no cabe en el tablero actual, guardar y abrir otro
            if y + pieza_alto > alto:
                tableros.append(posiciones)
                posiciones = []
                x, y, fila_alto = 0, 0, 0

            # Guardar pieza en el tablero actual
            posiciones.append((x, y, pieza_ancho, pieza_alto))
            x += pieza_ancho
            fila_alto = max(fila_alto, pieza_alto)

    # Guardar el último tablero en uso
    if posiciones:
        tableros.append(posiciones)

    return tableros


# Ejecutar el algoritmo
tableros = colocar_piezas_multi(piezas, TABLERO_ANCHO, TABLERO_ALTO)

# Dibujar cada tablero
for i, posiciones in enumerate(tableros, start=1):
    fig, ax = plt.subplots()
    ax.set_xlim(0, TABLERO_ANCHO)
    ax.set_ylim(0, TABLERO_ALTO)
    ax.set_aspect('equal')
    ax.set_title(f"Plan de corte - Tablero {i}")

    for (x, y, w, h) in posiciones:
        rect = plt.Rectangle((x, y), w, h, edgecolor='blue', facecolor='lightblue')
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, f"{w}x{h}", ha="center", va="center", fontsize=8)

    plt.show()
