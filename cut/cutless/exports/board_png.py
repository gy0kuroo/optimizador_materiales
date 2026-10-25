"""Exportación PNG de la geometría horizontal que presenta el visor."""
import io
import textwrap

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

from ..services.board_presentation import preparar_plano_horizontal
from ..units import convertir_desde_cm


def generar_png_tablero(vista, unidad, margen, numero, total, info, codigo=None, nombre=None):
    plano = preparar_plano_horizontal(vista, unidad, margen)
    catalogo = vista['catalogo']
    # Altura por contenido: la tabla crece sin reducir la letra del plano.
    rows = [max(1, len(textwrap.wrap(p['nombre'], 32))) for p in catalogo]
    table_height = .45 + sum(.34 * lines for lines in rows)
    board_height = 12 * plano['alto'] / plano['ancho'] + .8
    name_lines = textwrap.wrap(nombre or "", 72)
    name_height = .26*len(name_lines) + (.1 if name_lines else 0)
    height = 1 + board_height + table_height + .7 + name_height
    fig = Figure(figsize=(14, height), dpi=180, facecolor='white')
    FigureCanvasAgg(fig)
    fig.text(.055, 1-.35/height, f'{codigo} · Tablero {numero} de {total}' if codigo else f'Tablero {numero} de {total}',
             fontsize=17, weight='bold', color='#1C1008')
    if name_lines:
        fig.text(.055, 1-.65/height, '\n'.join(name_lines), fontsize=12, va='top')
    fig.text(.055, 1-(.65+name_height)/height,
             f"Aprovechamiento: {info.get('porcentaje_uso', 0):.2f}% · "
             f"Piezas: {info.get('num_piezas', 0)} · "
             f"Desperdicio: {info.get('desperdicio', 0):.2f} cm²", fontsize=11)
    ax = fig.add_axes([.065, (table_height+.7)/height, .9, board_height/height])
    ax.set_aspect('equal')
    ax.set_xlim(plano['origen'], plano['ancho']+plano['pad']*.3)
    ax.set_ylim(plano['alto']+plano['pad']*.3, plano['origen'])
    ax.axis('off')
    ax.add_patch(Rectangle((0, 0), plano['ancho'], plano['alto'],
                          facecolor='#F4F3EE', edgecolor='#4E2D01', linewidth=1))
    ax.plot([0, plano['ancho']], [plano['cota']]*2, color='#7D6344', linewidth=.7)
    ax.plot([plano['cota']]*2, [0, plano['alto']], color='#7D6344', linewidth=.7)
    ax.text(plano['centro_x'], plano['cota']-plano['pad']*.18,
            f"{plano['cota_ancho']:g} {unidad}", ha='center', va='bottom', fontsize=11)
    ax.text(plano['cota']-plano['pad']*.18, plano['centro_y'],
            f"{plano['cota_alto']:g} {unidad}", ha='right', va='center', rotation=90, fontsize=11)
    for resto in plano['sobrantes']:
        patch = Rectangle((resto['x'], resto['y']), resto['ancho'], resto['alto'],
                          facecolor='none', edgecolor='#B7B8AB', hatch='///', linewidth=.3)
        ax.add_patch(patch)
        if resto['mostrar_texto']:
            label = ax.text(resto['cx'], resto['cy'],
                    f"Sobrante\n{resto['medida_ancho']:g} × {resto['medida_alto']:g} {unidad}",
                    ha='center', va='center', fontsize=7, clip_on=True)
            label.set_clip_path(patch)
    for p in plano['piezas']:
        patch = Rectangle((p['x'], p['y']), p['ancho'], p['alto'],
                          facecolor=p['color'], edgecolor='#263238', linewidth=.8)
        ax.add_patch(patch)
        size = min(11, (p['texto'] if p['texto_detallado'] else p['texto_referencia']) * 12 * 72 / plano['ancho'])
        label = f"P{p['numero']}"
        if p['texto_detallado']:
            label += f"\n{p['nombre']}\n{p['medida_ancho']:g} × {p['medida_alto']:g} {unidad}"
        text = ax.text(p['cx'], p['cy'], label, ha='center', va='center',
                       fontsize=max(4, size), color='#1C1008', clip_on=True)
        text.set_clip_path(patch)
    table_ax = fig.add_axes([.055, .3/height, .9, table_height/height])
    table_ax.axis('off')
    cells = [[str(i), '\n'.join(textwrap.wrap(p['nombre'], 32)),
              f"{convertir_desde_cm(p['ancho'], unidad):g} × {convertir_desde_cm(p['alto'], unidad):g}",
              str(p['cantidad']), f"{p['ancho']*p['alto']*p['cantidad']/10000:.3f}", f"P{p['numero']}"]
             for i, p in enumerate(catalogo, 1)]
    table = table_ax.table(cellText=cells,
        colLabels=['#', 'Nombre de la pieza', f'Medidas ({unidad})', 'Cantidad', 'Área (m²)', 'Referencia'],
        colWidths=[.05, .36, .23, .11, .12, .13], cellLoc='left', bbox=[0, 0, 1, 1])
    table.auto_set_font_size(False); table.set_fontsize(10)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor('#B7B8AB'); cell.set_linewidth(.4)
        if row == 0:
            cell.set_facecolor('#F4F3EE'); cell.set_text_props(weight='bold')
        else:
            cell.set_height(.34 * rows[row-1]/table_height)
            if col == 5: cell.set_facecolor(catalogo[row-1]['color'])
    table_ax.set_title('Detalle de piezas', loc='left', fontsize=13, weight='bold', pad=12)
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=180)
    buffer.seek(0)
    return buffer
