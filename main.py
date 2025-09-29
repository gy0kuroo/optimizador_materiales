import matplotlib.pyplot as plt

# --- 1. Ingreso de datos por consola ---
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

# --- 2. Algoritmo simple de colocación en filas ---
def colocar_piezas(piezas, ancho, alto):
    x, y = 0, 0
    fila_alto = 0
    posiciones = []

    for pieza_ancho, pieza_alto, cantidad in piezas:
        for _ in range(cantidad):
            if x + pieza_ancho > ancho:  # nueva fila
                x = 0
                y += fila_alto
                fila_alto = 0

            if y + pieza_alto > alto:  # no cabe en el tablero
                print("⚠️ Se necesita un nuevo tablero (esta versión solo dibuja el primero)")
                return posiciones

            posiciones.append((x, y, pieza_ancho, pieza_alto))
            x += pieza_ancho
            fila_alto = max(fila_alto, pieza_alto)

    return posiciones

# --- 3. Ejecutar ---
posiciones = colocar_piezas(piezas, TABLERO_ANCHO, TABLERO_ALTO)

# --- 4. Dibujar tablero ---
fig, ax = plt.subplots()
ax.set_xlim(0, TABLERO_ANCHO)
ax.set_ylim(0, TABLERO_ALTO)
ax.set_aspect('equal')
ax.set_title("Plan de corte - Tablero")

for (x, y, w, h) in posiciones:
    rect = plt.Rectangle((x, y), w, h, edgecolor='blue', facecolor='lightblue')
    ax.add_patch(rect)
    ax.text(x + w/2, y + h/2, f"{w}x{h}", ha="center", va="center", fontsize=8)

plt.show()
