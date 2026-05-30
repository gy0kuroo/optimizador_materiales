"""
Motor de empaquetado 2D — FFD + BSSF con kerf y rotación opcional.

Sin dependencias de Django, matplotlib ni exports. Todas las medidas en cm.
"""

EPS = 1e-9


def pieza_cabe_en_tablero(pieza_ancho_cm, pieza_alto_cm, tablero_ancho_cm, tablero_alto_cm, permitir_rotacion=True):
    """
    True si la pieza puede cortarse en una sola placa sin partirla
    (orientación original u orientación rotada 90° si permitir_rotacion).
    """
    w = float(pieza_ancho_cm)
    h = float(pieza_alto_cm)
    W = float(tablero_ancho_cm)
    H = float(tablero_alto_cm)
    if w <= W and h <= H:
        return True
    if permitir_rotacion and h <= W and w <= H:
        return True
    return False


def _kern_block(w, h, x, y, W, H, m):
    """Hueco ocupado tras colocar pieza; kerf solo si no toca borde derecho/inferior."""
    bw = float(w + (m if x + float(w) < W - EPS else 0))
    bh = float(h + (m if y + float(h) < H - EPS else 0))
    return bw, bh


def _subtract_rect(ax, ay, aw, ah, bx, by, bw, bh, eps=EPS):
    """Parte el rectángulo A\\(A∩B) en hasta 4 rectángulos."""
    ix0 = max(ax, bx)
    iy0 = max(ay, by)
    ix1 = min(ax + aw, bx + bw)
    iy1 = min(ay + ah, by + bh)
    if ix0 >= ix1 - eps or iy0 >= iy1 - eps:
        return [(ax, ay, aw, ah)]
    chunks = []
    if iy0 > ay + eps:
        chunks.append((ax, ay, aw, iy0 - ay))
    if ay + ah > iy1 + eps:
        chunks.append((ax, iy1, aw, ay + ah - iy1))
    mh = iy1 - iy0
    if ix0 > ax + eps:
        chunks.append((ax, iy0, ix0 - ax, mh))
    if ax + aw > ix1 + eps:
        chunks.append((ix1, iy0, ax + aw - ix1, mh))
    return [(x, y, rw, rh) for x, y, rw, rh in chunks if rw > eps and rh > eps]


def _merge_free_rects(rects, eps=EPS):
    """Elimina rectángulos totalmente contenidos en otro."""
    rects = [(float(x), float(y), float(w), float(h)) for x, y, w, h in rects if w > eps and h > eps]
    kept = []
    n = len(rects)
    for i in range(n):
        x, y, w, h = rects[i]
        x2, y2 = x + w, y + h
        inside_other = False
        for j in range(n):
            if i == j:
                continue
            ox, oy, ow, oh = rects[j]
            if (
                ox - eps <= x
                and oy - eps <= y
                and ox + ow + eps >= x2
                and oy + oh + eps >= y2
            ):
                inside_other = True
                break
        if not inside_other:
            kept.append((x, y, w, h))
    return kept


def _fuse_adjacent_free_rects(rects, eps=1e-5):
    """Une rectángulos libres adyacentes del mismo ancho o altura."""
    rects = [(float(x), float(y), float(w), float(h)) for x, y, w, h in rects if w > eps and h > eps]
    changed = True
    while changed and len(rects) > 1:
        changed = False
        n = len(rects)
        for i in range(n):
            for j in range(i + 1, n):
                ax, ay, aw, ah = rects[i]
                bx, by, bw, bh = rects[j]
                if abs(ax - bx) < eps and abs(aw - bw) < eps:
                    if abs((ay + ah) - by) < eps or abs((by + bh) - ay) < eps:
                        y0 = min(ay, by)
                        y1 = max(ay + ah, by + bh)
                        merged = (ax, y0, aw, y1 - y0)
                        rects = [merged] + [rects[k] for k in range(n) if k not in (i, j)]
                        changed = True
                        break
                if abs(ay - by) < eps and abs(ah - bh) < eps:
                    if abs((ax + aw) - bx) < eps or abs((bx + bw) - ax) < eps:
                        x0 = min(ax, bx)
                        x1 = max(ax + aw, bx + bw)
                        merged = (x0, ay, x1 - x0, ah)
                        rects = [merged] + [rects[k] for k in range(n) if k not in (i, j)]
                        changed = True
                        break
            if changed:
                break
    return rects


def _normalizar_rects_libres(rects, eps=1e-5):
    """Contención + fusión de adyacentes hasta estabilizar."""
    r = _merge_free_rects(rects)
    prev = None
    while prev != r:
        prev = r
        r = _fuse_adjacent_free_rects(r, eps)
        r = _merge_free_rects(r)
    return r


def optimizar_corte(
    piezas,
    ancho_tablero,
    alto_tablero,
    permitir_rotacion=True,
    margen_corte=0.3,
    nombres_piezas=None,
):
    """
    Coloca piezas en tableros con FFD + BSSF.

    Args:
        piezas: lista de (ancho_cm, alto_cm, cantidad)
        ancho_tablero, alto_tablero: dimensiones en cm
        margen_corte: kerf en cm entre cortes vecinos

    Returns:
        (tableros, aprovechamiento_total, info_desperdicio)
        tableros: lista de dicts con clave 'posiciones' (tuplas x,y,w,h,rotada,wo,ho,nombre)
        info_desperdicio: mismo dict que generar_grafico devuelve como tercer valor
    """
    area_tablero = ancho_tablero * alto_tablero
    tableros = []
    area_usada_total = 0
    piezas_no_colocadas = []
    num_piezas_solicitadas = sum(int(c) for _, _, c in piezas)

    piezas_expandidas = []
    for idx, (w, h, c) in enumerate(piezas):
        if nombres_piezas and idx < len(nombres_piezas):
            nombre_base = nombres_piezas[idx].strip() or f"Pieza {idx + 1}"
        else:
            nombre_base = f"Pieza {idx + 1}"
        for _ in range(c):
            piezas_expandidas.append({
                'ancho': w,
                'alto': h,
                'area': w * h,
                'original': (w, h),
                'rotada': False,
                'nombre': nombre_base,
            })

    piezas_expandidas.sort(key=lambda x: x['area'], reverse=True)

    w_bin = float(ancho_tablero)
    h_bin = float(alto_tablero)
    kerf = float(margen_corte)

    def _calcular_desperdicio(tablero):
        area_usada = 0
        for pos in tablero['posiciones']:
            if len(pos) >= 5:
                _, _, wg, hg, _ = pos[:5]
                area_usada += wg * hg
        return area_tablero - area_usada

    def _tb_clonar(tb):
        return {
            'posiciones': list(tb['posiciones']),
            'free_rects': [(float(a), float(b), float(fw), float(fh)) for a, b, fw, fh in tb['free_rects']],
        }

    def _tb_vacio():
        return {'posiciones': [], 'free_rects': [(0.0, 0.0, w_bin, h_bin)]}

    def _mejor_ancla_bssf(tablero, wg, hg):
        best_key = None
        anchor = None
        for fx, fy, fw, fh in tablero['free_rects']:
            if fx + wg > w_bin + EPS or fy + hg > h_bin + EPS:
                continue
            bw, bh = _kern_block(wg, hg, fx, fy, w_bin, h_bin, kerf)
            if bw > fw + EPS or bh > fh + EPS:
                continue
            key = (fw - bw, fh - bh, fy, fx)
            if best_key is None or key < best_key:
                best_key = key
                anchor = (fx, fy, bw, bh)
        return anchor

    def _aplicar_pieza(tablero, gx, gy, bw, bh, wg, hg, rotada, wo, ho, nombre):
        tablero['posiciones'].append((gx, gy, wg, hg, rotada, wo, ho, nombre))
        nueva = []
        for fx, fy, fw, fh in tablero['free_rects']:
            nueva.extend(_subtract_rect(fx, fy, fw, fh, gx, gy, bw, bh))
        tablero['free_rects'] = _normalizar_rects_libres(nueva)

    def _intentar_colocacion(tb_orig, pieza, wg, hg, rotada):
        cand = _tb_clonar(tb_orig)
        pack = _mejor_ancla_bssf(cand, wg, hg)
        if pack is None:
            return None
        gx, gy, bw, bh = pack
        _aplicar_pieza(
            cand, gx, gy, bw, bh, wg, hg, rotada,
            pieza['ancho'], pieza['alto'], pieza.get('nombre', 'Pieza'),
        )
        return cand

    def _considerar(best, nuevo_key, payload):
        if best is None or nuevo_key < best[0]:
            return (nuevo_key, payload)
        return best

    for pieza in piezas_expandidas:
        w_original = pieza['ancho']
        h_original = pieza['alto']
        if permitir_rotacion and w_original != h_original:
            orientaciones = [(w_original, h_original, False), (h_original, w_original, True)]
        else:
            orientaciones = [(w_original, h_original, False)]

        mejor = None

        for wg, hg, rot in orientaciones:
            if wg > w_bin + EPS or hg > h_bin + EPS:
                continue

            for tbi, tb in enumerate(tableros):
                prob = _intentar_colocacion(tb, pieza, wg, hg, rot)
                if prob is None:
                    continue
                desp = _calcular_desperdicio(prob)
                k = (desp, 1 if rot else 0, tbi)
                mejor = _considerar(mejor, k, ('existe', tbi, prob, rot))

            nueva_hoja = _intentar_colocacion(_tb_vacio(), pieza, wg, hg, rot)
            if nueva_hoja is None:
                continue
            desp_n = _calcular_desperdicio(nueva_hoja)
            k_n = (desp_n, 1 if rot else 0, len(tableros) + 1)
            mejor = _considerar(mejor, k_n, ('nuevo', nueva_hoja, rot))

        if mejor is None:
            piezas_no_colocadas.append({
                'nombre': pieza.get('nombre', 'Pieza'),
                'ancho_cm': w_original,
                'alto_cm': h_original,
            })
            continue

        _, payload = mejor
        if payload[0] == 'existe':
            _, tbi, nueva_tb, rot = payload
            tableros[tbi] = nueva_tb
            pieza['rotada'] = rot
        else:
            _, nueva_tb, rot = payload
            tableros.append(nueva_tb)
            pieza['rotada'] = rot
        area_usada_total += w_original * h_original

    num_tableros = len(tableros)
    num_piezas_colocadas = sum(len(t['posiciones']) for t in tableros)
    if num_tableros == 0:
        aprovechamiento_total = 0
        desperdicio_total = 0
        info_tableros = []
    else:
        area_total_disponible = num_tableros * area_tablero
        desperdicio_total = area_total_disponible - area_usada_total
        aprovechamiento_total = round((area_usada_total / area_total_disponible) * 100, 2)
        info_tableros = []
        for idx, tablero in enumerate(tableros, start=1):
            area_usada_tablero = 0
            for pos in tablero['posiciones']:
                if len(pos) >= 5:
                    _, _, w, h, _ = pos[:5]
                    area_usada_tablero += w * h
            desperdicio_tablero = area_tablero - area_usada_tablero
            porcentaje_uso = round((area_usada_tablero / area_tablero) * 100, 2)
            info_tableros.append({
                'numero': idx,
                'area_usada': area_usada_tablero,
                'desperdicio': desperdicio_tablero,
                'porcentaje_uso': porcentaje_uso,
                'num_piezas': len(tablero['posiciones']),
            })

    info = {
        'area_usada_total': area_usada_total,
        'desperdicio_total': desperdicio_total,
        'info_tableros': info_tableros,
        'num_tableros': num_tableros,
        'area_total_disponible': num_tableros * area_tablero if num_tableros > 0 else 0,
        'piezas_no_colocadas': piezas_no_colocadas,
        'num_piezas_solicitadas': num_piezas_solicitadas,
        'num_piezas_colocadas': num_piezas_colocadas,
    }
    return tableros, aprovechamiento_total, normalizar_info_desperdicio(info)


INFO_DESPERDICIO_CAMPOS = (
    'area_usada_total',
    'desperdicio_total',
    'info_tableros',
    'num_tableros',
    'area_total_disponible',
    'piezas_no_colocadas',
    'num_piezas_solicitadas',
    'num_piezas_colocadas',
)


def normalizar_info_desperdicio(info_desperdicio, *, area_usada_total=None, desperdicio_total=None):
    """
    Garantiza el dict completo de resultado de optimización (áreas en cm²).
    Tolera dicts parciales o el de un solo tablero.
    """
    raw = dict(info_desperdicio or {})

    info_tableros = raw.get('info_tableros')
    if not info_tableros and 'numero' in raw:
        info_tableros = [{
            'numero': raw.get('numero', 1),
            'area_usada': raw.get('area_usada', 0) or 0,
            'desperdicio': raw.get('desperdicio', 0) or 0,
            'porcentaje_uso': raw.get('porcentaje_uso', 0) or 0,
            'num_piezas': raw.get('num_piezas', 0) or 0,
        }]
    info_tableros = list(info_tableros or [])

    au = raw.get('area_usada_total')
    if au is None:
        au = area_usada_total
    if au is None and 'area_usada' in raw and 'numero' in raw:
        au = raw.get('area_usada', 0)
    if au is None:
        au = sum(float(t.get('area_usada', 0) or 0) for t in info_tableros)

    dt = raw.get('desperdicio_total')
    if dt is None:
        dt = desperdicio_total
    if dt is None and 'desperdicio' in raw and 'numero' in raw:
        dt = raw.get('desperdicio', 0)
    if dt is None:
        dt = sum(float(t.get('desperdicio', 0) or 0) for t in info_tableros)

    au = float(au or 0)
    dt = float(dt or 0)

    num_tableros = raw.get('num_tableros')
    if num_tableros is None:
        num_tableros = len(info_tableros)

    num_colocadas = raw.get('num_piezas_colocadas')
    if num_colocadas is None:
        num_colocadas = sum(int(t.get('num_piezas', 0) or 0) for t in info_tableros)

    return {
        'area_usada_total': au,
        'desperdicio_total': dt,
        'info_tableros': info_tableros,
        'num_tableros': num_tableros,
        'area_total_disponible': float(raw.get('area_total_disponible', au + dt) or 0),
        'piezas_no_colocadas': raw.get('piezas_no_colocadas') or [],
        'num_piezas_solicitadas': int(raw.get('num_piezas_solicitadas') or 0),
        'num_piezas_colocadas': int(num_colocadas or 0),
    }
