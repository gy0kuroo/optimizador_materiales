"""Renderizado de tableros y graficos estadisticos (matplotlib)."""
import base64
import io

import matplotlib
matplotlib.use('Agg')
import matplotlib.dates as mdates
import matplotlib.patches as patches
from matplotlib.gridspec import GridSpec
import matplotlib.pyplot as plt

from .packing import optimizar_corte, normalizar_info_desperdicio
from .pieces import parsear_piezas_desde_texto
from .units import convertir_desde_cm, obtener_simbolo_area, obtener_simbolo_unidad

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

def _dibujar_leyenda_tipos_piezas(ax_leg, catalogo_ord, numero_por_tipo, color_por_tipo, unidad, cantidad_por_tipo):
    ax_leg.axis('off')
    entries = [k for k in catalogo_ord if cantidad_por_tipo.get(k, 0) > 0]
    n = len(entries)
    if n == 0:
        ax_leg.set_xlim(0, 1)
        ax_leg.set_ylim(0, 1)
        return

    simbolo = obtener_simbolo_unidad(unidad)
    fs = 8
    lh = 11
    rh = 66
    top_pad = 16
    total_h = n * rh + top_pad + 8
    ax_leg.set_xlim(0, 100)
    ax_leg.set_ylim(0, total_h)

    ax_leg.text(
        4, total_h - 4, 'Descripción de piezas',
        fontsize=11, fontweight='bold', va='top', color='#111',
    )

    for i, key in enumerate(entries):
        nombre_t, wc, hc = key
        num_t = numero_por_tipo[key]
        clr = color_por_tipo[key]
        cantidad = cantidad_por_tipo[key]
        wd = round(convertir_desde_cm(wc, unidad), 1)
        hd = round(convertir_desde_cm(hc, unidad), 1)
        row_top = total_h - top_pad - i * rh
        y = row_top - 4

        texto_n = nombre_t[:32] + ('…' if len(nombre_t) > 32 else '')
        lineas = [
            f'Número: {num_t}',
            f'Nombre: {texto_n}',
            f'Medidas: {wd} × {hd} {simbolo}',
            f'Cantidad de piezas: {cantidad}',
        ]
        for j, linea in enumerate(lineas):
            ax_leg.text(
                4, y - j * lh, linea,
                fontsize=fs, va='top', ha='left', color='#111',
            )

        color_y = y - len(lineas) * lh
        ax_leg.text(4, color_y, 'Color:', fontsize=fs, va='top', ha='left', color='#111')
        ax_leg.add_patch(patches.Rectangle(
            (24, color_y - 7.5),
            10,
            8,
            linewidth=1,
            edgecolor='#2c3e50',
            facecolor=clr,
            alpha=0.9,
        ))
        ax_leg.text(38, color_y, clr.upper(), fontsize=fs, va='top', ha='left', color='#444')

        if i < n - 1:
            sep_y = row_top - rh + 4
            ax_leg.plot([4, 96], [sep_y, sep_y], color='#ddd', linewidth=0.8)

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

        fig = plt.figure(figsize=(12.5, 9.8))
        gs = GridSpec(1, 2, figure=fig, width_ratios=[1, 0.44], wspace=0.10)
        ax = fig.add_subplot(gs[0, 0])
        ax_leg = fig.add_subplot(gs[0, 1])
        fig.subplots_adjust(left=0.05, right=0.96, top=0.91, bottom=0.06)

        ax.set_xlim(0, ancho_tablero)
        ax.set_ylim(0, alto_tablero)
        ax.invert_yaxis()
        ax.set_aspect('equal')
        
        # Convertir desperdicio para mostrar
        simbolo = obtener_simbolo_unidad(unidad)
        simbolo_area = obtener_simbolo_area(unidad)
        factor_lineal = convertir_desde_cm(1, unidad)
        factor_area = factor_lineal ** 2
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
                        fontsize=13, fontweight='bold', pad=20)
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

            # Información detallada (solo en modo normal)
            area_usada_mostrar = round(info_tablero['area_usada'] * factor_area, 2)
            info_text = (f"Piezas: {info_tablero['num_piezas']}\n"
                        f"Área usada: {area_usada_mostrar} {simbolo_area}\n"
                        f"Desperdicio: {desperdicio_mostrar} {simbolo_area}")
            ax.text(ancho_tablero * 0.02, alto_tablero * 0.98, info_text,
                   fontsize=9, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))

        cantidad_por_tipo_tablero = {}
        for ji, pd in enumerate(posiciones):
            key_tv = _tipo_pieza_visual_key(pd, ji)
            cantidad_por_tipo_tablero[key_tv] = cantidad_por_tipo_tablero.get(key_tv, 0) + 1

        _dibujar_leyenda_tipos_piezas(
            ax_leg, catalogo_ord, numero_por_tipo, color_por_tipo,
            unidad, cantidad_por_tipo_tablero,
        )

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=120, bbox_inches='tight', facecolor='white')
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
    margen_corte = getattr(optimizacion, 'margen_corte', 0.3) or 0.3
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
