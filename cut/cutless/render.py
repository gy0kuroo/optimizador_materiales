"""Renderizado de tableros y graficos estadisticos (matplotlib)."""
import base64
import io
import textwrap

import matplotlib
matplotlib.use('Agg')
import matplotlib.dates as mdates
from matplotlib.textpath import TextPath
import matplotlib.patches as patches
from matplotlib.gridspec import GridSpec
import matplotlib.pyplot as plt

from .packing import optimizar_corte, normalizar_info_desperdicio
from .pieces import parsear_piezas_desde_texto
from .units import convertir_desde_cm, obtener_factor_area_desde_cm2, obtener_simbolo_area, obtener_simbolo_unidad

def _unpack_posicion_grafico(pos_data, idx_fallback):
    """Normaliza cualquier formato de tupla ``posiciones``."""
    nombre_pieza = f'Pieza {idx_fallback + 1}'
    rotada = False
    x, y, w, h = pos_data[:4]
    if len(pos_data) >= 8:
        x, y, w, h, rotada, w_orig, h_orig, nombre_pieza = pos_data[:8]
    elif len(pos_data) == 7:
        x, y, w, h, rotada, w_orig, h_orig = pos_data
    elif len(pos_data) == 5:
        x, y, w, h, rotada = pos_data[:5]
        w_orig, h_orig = w, h
    else:
        w_orig, h_orig = w, h
    nombre = (str(nombre_pieza).strip() or nombre_pieza) or f'Pieza {idx_fallback + 1}'
    return float(x), float(y), float(w), float(h), rotada, float(w_orig), float(h_orig), nombre

def _tipo_pieza_visual_key(pos_data, idx_fallback):
    """Clave estable: mismo nombre + medidas solicitadas ⇒ mismo color."""
    _, _, _, _, _, wo, ho, nombre = _unpack_posicion_grafico(pos_data, idx_fallback)
    return (nombre, round(wo, 6), round(ho, 6))

def _catalogo_tipos_piezas_visual(tableros):
    seen = set()
    for tb in tableros:
        for ji, pd in enumerate(tb['posiciones']):
            seen.add(_tipo_pieza_visual_key(pd, ji))
    return sorted(seen, key=lambda t: (t[0].lower(), t[1], t[2]))

def _paleta_tipos_visual(n):
    """Colores suficientemente distintos; se cicla si hay muchos tipos."""
    base = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2',
        '#E74C3C', '#3498DB', '#27AE60', '#9B59B6', '#1ABC9C', '#F39C12', '#5DADE2', '#AF7AC5',
        '#DC7633', '#48C9B0', '#EC7063', '#52BE80', '#839192', '#C39BD3',
    ]
    out = []
    i = 0
    while len(out) < n:
        out.append(base[i % len(base)])
        i += 1
    return out

def _filas_leyenda(catalogo_ord, numero_por_tipo, unidad, cantidad_por_tipo):
    """Filas compactas, con altura suficiente para conservar nombres completos."""
    simbolo = obtener_simbolo_unidad(unidad)
    filas = []
    for clave in catalogo_ord:
        cantidad = cantidad_por_tipo.get(clave, 0)
        if cantidad <= 0:
            continue
        nombre, ancho, alto = clave
        # Medir el texto evita que nombres anchos invadan la columna de medidas.
        limite = 24
        original = nombre
        nombre = textwrap.fill(original, width=limite)
        while limite > 1 and any(TextPath((0, 0), linea, size=12).get_extents().width > 100
                                 for linea in nombre.splitlines() if linea.strip()):
            limite -= 1
            nombre = textwrap.fill(original, width=limite)
        medidas = (f"{convertir_desde_cm(ancho, unidad):g} × "
                   f"{convertir_desde_cm(alto, unidad):g} {simbolo}")
        lineas = max(1, len(nombre.splitlines()))
        filas.append((clave, [str(numero_por_tipo[clave]), nombre, medidas, str(cantidad)],
                      .42 + .20 * (lineas - 1)))
    return filas


def _dibujar_leyenda_tipos_piezas(ax_leg, catalogo_ord, numero_por_tipo, color_por_tipo, unidad, cantidad_por_tipo):
    ax_leg.axis('off')
    filas = _filas_leyenda(catalogo_ord, numero_por_tipo, unidad, cantidad_por_tipo)
    if not filas:
        return
    ax_leg.text(0, 1, 'Piezas de este tablero', transform=ax_leg.transAxes,
                fontsize=15, fontweight='bold', va='top', color='#1C1008')
    altura_eje = ax_leg.get_position().height * ax_leg.figure.get_figheight()
    altura_tabla = (.40 + sum(fila[2] for fila in filas)) / altura_eje
    tabla = ax_leg.table(
        cellText=[fila[1] for fila in filas],
        colLabels=['N.º', 'Pieza', 'Medidas', 'Cant.'],
        colWidths=[.09, .43, .33, .15], cellLoc='left',
        bbox=[0, 1 - .55 / altura_eje - altura_tabla, 1, altura_tabla],
    )
    tabla.auto_set_font_size(False)
    tabla.set_fontsize(12)
    for (fila, columna), celda in tabla.get_celld().items():
        celda.set_edgecolor('#C8C5B8')
        celda.set_linewidth(.7)
        celda.PAD = .10
        celda.get_text().set_color('#1C1008')
        celda.get_text().set_parse_math(False)
        if fila == 0:
            celda.set_facecolor('#ECEAE2')
            celda.get_text().set_fontweight('bold')
            celda.set_height(.40 / altura_eje)
        else:
            clave, _, altura = filas[fila - 1]
            celda.set_height(altura / altura_eje)
            celda.set_facecolor('#FFFFFF')
            if columna == 0:
                celda.set_facecolor(color_por_tipo[clave])
                celda.get_text().set_fontweight('bold')
            if columna in (0, 3):
                celda.get_text().set_ha('center')
    ax_leg.text(0, 1 - .55 / altura_eje - altura_tabla - .16 / altura_eje,
                'Medidas solicitadas · Cantidades en este tablero',
                transform=ax_leg.transAxes, fontsize=10, color='#5A4535', va='top')


def _numero_interior_pieza(num_tipo, w_placed_cm, h_placed_cm, ancho_tb_cm, alto_tb_cm):
    """Devuelve (texto o None, fontsize)."""
    min_tab = max(min(ancho_tb_cm, alto_tb_cm), 1e-9)
    rel = min(w_placed_cm, h_placed_cm) / min_tab
    if rel < 0.035:
        return None, None
    fs = max(6, min(15, min_tab / 8 + rel * 48))
    return str(num_tipo), fs

def generar_grafico(piezas, ancho_tablero, alto_tablero, unidad='cm', permitir_rotacion=True, margen_corte=0.3, nombres_piezas=None, modo_plan_corte=False):
    """
    Ejecuta el motor de corte (FFD + BSSF) y genera imágenes PNG en base64.

    Args:
        piezas: Lista de tuplas (ancho, alto, cantidad) en cm
        ancho_tablero: Ancho del tablero en cm
        alto_tablero: Alto del tablero en cm
        unidad: Unidad de medida para mostrar
        permitir_rotacion: Si True, intenta rotar piezas 90° si mejora el aprovechamiento
        margen_corte: Margen de corte (kerf) en cm entre cortes vecinos (no sobre borde placa).
        nombres_piezas: Lista opcional de nombres para la etiqueta en el gráfico
    """
    tableros, aprovechamiento_total, info_desperdicio = optimizar_corte(
        piezas,
        ancho_tablero,
        alto_tablero,
        permitir_rotacion=permitir_rotacion,
        margen_corte=margen_corte,
        nombres_piezas=nombres_piezas,
    )
    info_tableros = info_desperdicio['info_tableros']
    num_tableros = info_desperdicio['num_tableros']

    # Leyenda/colores consistentes entre tableros (nombre + medidas solicitadas)
    catalogo_ord = _catalogo_tipos_piezas_visual(tableros)
    numero_por_tipo = {k: i + 1 for i, k in enumerate(catalogo_ord)}
    paleta_visual = _paleta_tipos_visual(len(catalogo_ord))
    color_por_tipo = {k: paleta_visual[j] for j, k in enumerate(catalogo_ord)}

    # Generar imágenes
    imagenes_base64 = []

    for i, tablero in enumerate(tableros, start=1):
        posiciones = tablero['posiciones']
        info_tablero = info_tableros[i-1]

        # La vista web guarda la misma distribución que el PNG, sin recalcularla al leer.
        cantidades_web = {}
        piezas_web = []
        for indice, posicion in enumerate(posiciones):
            x, y, w, h, rotada, _, _, nombre = _unpack_posicion_grafico(posicion, indice)
            clave = _tipo_pieza_visual_key(posicion, indice)
            cantidades_web[clave] = cantidades_web.get(clave, 0) + 1
            piezas_web.append({'x': x, 'y': y, 'ancho': w, 'alto': h,
                               'centro_x': x + w / 2, 'centro_y': y + h / 2,
                               'numero': numero_por_tipo[clave], 'color': color_por_tipo[clave],
                               'nombre': nombre, 'rotada': bool(rotada),
                               'mostrar_numero': min(w, h) >= min(ancho_tablero, alto_tablero) * .04})
        info_tablero['vista_web'] = {
            'ancho': float(ancho_tablero), 'alto': float(alto_tablero),
            'tamano_numero': min(ancho_tablero, alto_tablero) * .055,
            'piezas': piezas_web,
            'catalogo': [{'numero': numero_por_tipo[clave], 'nombre': clave[0],
                          'ancho': clave[1], 'alto': clave[2], 'color': color_por_tipo[clave],
                          'cantidad': cantidades_web[clave]}
                         for clave in catalogo_ord if clave in cantidades_web],
        }

        cantidades_leyenda = cantidades_web
        filas_leyenda = _filas_leyenda(catalogo_ord, numero_por_tipo, unidad, cantidades_leyenda)
        altura_figura = max(9.8, (2.1 + sum(fila[2] for fila in filas_leyenda)) / .85)
        fig = plt.figure(figsize=(11.5, altura_figura))
        gs = GridSpec(1, 2, figure=fig, width_ratios=[1, 1.15], wspace=0.12)
        ax = fig.add_subplot(gs[0, 0])
        ax_leg = fig.add_subplot(gs[0, 1])
        fig.subplots_adjust(left=0.05, right=0.96, top=0.91, bottom=0.06)

        ax.set_xlim(0, ancho_tablero)
        ax.set_ylim(0, alto_tablero)
        ax.invert_yaxis()
        ax.set_aspect('equal')
        ax.set_anchor('E')
        
        # Convertir desperdicio para mostrar
        simbolo = obtener_simbolo_unidad(unidad)
        simbolo_area = obtener_simbolo_area(unidad)
        factor_area = obtener_factor_area_desde_cm2(unidad)
        desperdicio_mostrar = round(info_tablero['desperdicio'] * factor_area, 2)
        
        # Título y configuración según modo
        if modo_plan_corte:
            # Modo plan de corte: sin título, solo dimensiones del tablero
            ax.set_title(f"{ancho_tablero} × {alto_tablero} {simbolo}",
                        fontsize=12, fontweight='bold', pad=10)
            ax.set_xlabel(f"Ancho ({simbolo})", fontsize=10)
            ax.set_ylabel(f"Alto ({simbolo})", fontsize=10)
            ax.grid(True, alpha=0.2, linestyle='-', linewidth=0.5, color='gray')
        else:
            # Modo normal: con información completa
            ax.set_title(f"Tablero {i} de {num_tableros} - FFD + rect. libres\n"
                        f"Uso: {info_tablero['porcentaje_uso']}% | Desperdicio: {desperdicio_mostrar} {simbolo_area}",
                        fontsize=15, fontweight='bold', pad=16)
            ax.set_xlabel(f"Ancho ({simbolo})", fontsize=11)
            ax.set_ylabel(f"Alto ({simbolo})", fontsize=11)
            ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        
        ax.set_axisbelow(True)
        
        # Borde del tablero
        if modo_plan_corte:
            borde = patches.Rectangle((0, 0), ancho_tablero, alto_tablero,
                                      linewidth=2, edgecolor='black', 
                                      facecolor='white', alpha=1.0)
        else:
            borde = patches.Rectangle((0, 0), ancho_tablero, alto_tablero,
                                      linewidth=3, edgecolor='black', 
                                      facecolor='#f0f0f0', alpha=0.3)
        ax.add_patch(borde)
        
        # Dibujar piezas
        if modo_plan_corte:
            for idx, pos_data in enumerate(posiciones):
                x, y, w, h, rotada, _wo, _ho, _nom = _unpack_posicion_grafico(pos_data, idx)
                key_tv = _tipo_pieza_visual_key(pos_data, idx)
                num_t = numero_por_tipo[key_tv]
                clr = color_por_tipo[key_tv]
                ax.add_patch(patches.Rectangle(
                    (x, y), w, h, linewidth=2.8, edgecolor=clr,
                    facecolor='white', alpha=1.0,
                ))
                texto_n, psz = _numero_interior_pieza(num_t, w, h, ancho_tablero, alto_tablero)
                if texto_n:
                    ax.text(
                        x + w / 2, y + h / 2,
                        texto_n,
                        fontsize=psz, ha='center', va='center', fontweight='bold',
                        color='#1a1f2c',
                    )
        else:
            for idx, pos_data in enumerate(posiciones):
                x, y, w, h, rotada, _wo, _ho, _nom = _unpack_posicion_grafico(pos_data, idx)
                key_tv = _tipo_pieza_visual_key(pos_data, idx)
                clr = color_por_tipo[key_tv]
                num_t = numero_por_tipo[key_tv]
                ax.add_patch(patches.Rectangle(
                    (x, y), w, h, linewidth=2,
                    edgecolor='#263238', facecolor=clr, alpha=0.78,
                ))
                texto_n, psz = _numero_interior_pieza(num_t, w, h, ancho_tablero, alto_tablero)
                if texto_n:
                    ax.text(
                        x + w / 2, y + h / 2,
                        texto_n,
                        fontsize=psz, ha='center', va='center', fontweight='bold',
                        color='#102027',
                    )

        cantidad_por_tipo_tablero = {}
        for ji, pd in enumerate(posiciones):
            key_tv = _tipo_pieza_visual_key(pd, ji)
            cantidad_por_tipo_tablero[key_tv] = cantidad_por_tipo_tablero.get(key_tv, 0) + 1

        _dibujar_leyenda_tipos_piezas(
            ax_leg, catalogo_ord, numero_por_tipo, color_por_tipo,
            unidad, cantidad_por_tipo_tablero,
        )

        if not modo_plan_corte:
            altura_eje = ax_leg.get_position().height * fig.get_figheight()
            resumen_y = 1 - (1.45 + sum(fila[2] for fila in filas_leyenda)) / altura_eje
            area_usada_mostrar = round(info_tablero['area_usada'] * factor_area, 2)
            ax_leg.text(0, resumen_y,
                        f"Piezas: {info_tablero['num_piezas']}\n"
                        f"Área usada: {area_usada_mostrar} {simbolo_area}\n"
                        f"Desperdicio: {desperdicio_mostrar} {simbolo_area}",
                        transform=ax_leg.transAxes, fontsize=11, color='#5A4535',
                        va='top', linespacing=1.5)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=160, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        buf.seek(0)
        imagenes_base64.append(base64.b64encode(buf.read()).decode("utf-8"))

    return imagenes_base64, aprovechamiento_total, normalizar_info_desperdicio(info_desperdicio)

def _info_desperdicio_desde_optimizacion(optimizacion):
    """Regenera el dict info_desperdicio sin generar imágenes."""
    unidad_opt = getattr(optimizacion, 'unidad_medida', 'cm') or 'cm'
    piezas_parseadas = parsear_piezas_desde_texto(optimizacion.piezas, unidad_opt)
    if not piezas_parseadas:
        return None

    piezas = [
        (p['ancho_cm'], p['alto_cm'], p['cantidad'])
        for p in piezas_parseadas
    ]
    nombres_piezas = [p['nombre'] for p in piezas_parseadas]
    permitir_rotacion = getattr(optimizacion, 'permitir_rotacion', True)
    margen_corte = getattr(optimizacion, 'margen_corte', 0.3)
    if margen_corte is None:
        margen_corte = 0.3
    _, _, info = optimizar_corte(
        piezas,
        optimizacion.ancho_tablero,
        optimizacion.alto_tablero,
        permitir_rotacion=permitir_rotacion,
        margen_corte=margen_corte,
        nombres_piezas=nombres_piezas if nombres_piezas else None,
    )
    return info

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
            color='#4558E7', label='Aprovechamiento')
    
    # Línea de promedio
    ax.axhline(y=promedio, color='#7D6344', linestyle='--', linewidth=linewidth,
               label=f'Promedio: {promedio:.2f}%')
    
    # Formatear fechas según período
    if periodo == 'semanal':
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    elif periodo == 'mensual':
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    elif periodo == 'anual':
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%Y'))
    else:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
    
    plt.xticks(rotation=45, ha='right')
    ax.set_xlabel('Fecha', fontsize=fontsize_labels, fontweight='bold')
    ax.set_ylabel('Aprovechamiento (%)', fontsize=fontsize_labels, fontweight='bold')
    ax.set_title('Tendencia de aprovechamiento', fontsize=fontsize_title, fontweight='bold', pad=20)
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
            color='#7D6344', label='Desperdicio')
    
    # Línea de promedio
    ax.axhline(y=promedio, color='#4558E7', linestyle='--', linewidth=linewidth,
               label=f'Promedio: {promedio:.2f}%')
    
    # Formatear fechas según período
    if periodo == 'semanal':
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    elif periodo == 'mensual':
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    elif periodo == 'anual':
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%Y'))
    else:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
    
    plt.xticks(rotation=45, ha='right')
    ax.set_xlabel('Fecha', fontsize=fontsize_labels, fontweight='bold')
    ax.set_ylabel('Desperdicio (%)', fontsize=fontsize_labels, fontweight='bold')
    ax.set_title('Tendencia de desperdicio', fontsize=fontsize_title, fontweight='bold', pad=20)
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
