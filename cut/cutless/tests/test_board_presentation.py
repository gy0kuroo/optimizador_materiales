from copy import deepcopy

from django.test import SimpleTestCase

from cutless.services.board_presentation import preparar_plano_horizontal


class PlanoHorizontalTests(SimpleTestCase):
    def setUp(self):
        self.vista = {
            'ancho': 122, 'alto': 244,
            'catalogo': [{'numero': 4, 'nombre': 'Puerta', 'ancho': 40, 'alto': 120}],
            'piezas': [{'x': 10, 'y': 20, 'ancho': 40, 'alto': 120,
                        'numero': 4, 'nombre': 'Puerta', 'color': '#4558E7'}],
        }

    def test_gira_geometria_sin_mutar_datos_ni_medidas_solicitadas(self):
        antes = deepcopy(self.vista)
        plano = preparar_plano_horizontal(self.vista, 'cm', .3)
        self.assertEqual((plano['ancho'], plano['alto']), (244, 122))
        pieza = plano['piezas'][0]
        self.assertEqual((pieza['x'], pieza['y'], pieza['ancho'], pieza['alto']), (104, 10, 120, 40))
        self.assertEqual((pieza['medida_ancho'], pieza['medida_alto']), (40, 120))
        self.assertEqual(pieza['numero'], 4)
        self.assertEqual(self.vista, antes)

    def test_complemento_no_solapa_piezas_y_conserva_area_sin_sierra(self):
        plano = preparar_plano_horizontal(self.vista, 'cm', 0)
        rects = plano['piezas'] + plano['sobrantes']
        self.assertAlmostEqual(sum(r['ancho'] * r['alto'] for r in rects), 122 * 244)
        for i, a in enumerate(rects):
            for b in rects[i+1:]:
                overlap_x = min(a['x']+a['ancho'], b['x']+b['ancho'])-max(a['x'], b['x'])
                overlap_y = min(a['y']+a['alto'], b['y']+b['alto'])-max(a['y'], b['y'])
                self.assertTrue(overlap_x <= 1e-7 or overlap_y <= 1e-7)

    def test_no_gira_tablero_ya_horizontal_y_convierte_solo_textos(self):
        self.vista.update(ancho=244, alto=122)
        self.vista['piezas'][0].update(ancho=120, alto=40)
        plano = preparar_plano_horizontal(self.vista, 'm', .3)
        self.assertEqual(plano['piezas'][0]['x'], 10)
        self.assertEqual(plano['piezas'][0]['medida_ancho'], .4)
        self.assertEqual(plano['cota_ancho'], 2.44)

    def test_ranura_de_sierra_no_se_anuncia_como_sobrante(self):
        self.vista['piezas'][0].update(x=0, y=0, ancho=121.7, alto=244)
        plano = preparar_plano_horizontal(self.vista, 'cm', .3)
        self.assertEqual(plano['sobrantes'], [])

    def test_resultado_antiguo_no_inventa_coordenadas(self):
        self.assertIsNone(preparar_plano_horizontal(None, 'cm', .3))

    def test_pieza_pequena_muestra_referencia_mayor_sin_descripcion(self):
        self.vista['catalogo'].append(dict(numero=3,nombre='Pequeña',ancho=10,alto=10))
        self.vista['piezas'].append(dict(numero=3,nombre='Pequeña',color='#4558E7',
            x=0,y=0,ancho=10,alto=10))
        plano = preparar_plano_horizontal(self.vista, 'cm', .3)
        self.assertTrue(plano['piezas'][0]['texto_detallado'])
        pequena = plano['piezas'][1]
        self.assertFalse(pequena['texto_detallado'])
        self.assertGreater(pequena['texto_referencia'], pequena['texto'])

    def test_sobrante_estrecho_solo_rayado(self):
        self.vista['piezas'][0].update(x=0,y=0,ancho=112,alto=244)
        plano = preparar_plano_horizontal(self.vista,'cm',.3)
        self.assertTrue(plano['sobrantes'])
        self.assertTrue(all(not r['mostrar_texto'] for r in plano['sobrantes']))

    def test_svg_conserva_detalle_en_title_y_recorta_etiquetas(self):
        from django.template.loader import render_to_string
        from xml.etree import ElementTree as ET
        self.vista['catalogo'][0].update(ancho=10,alto=10)
        self.vista['piezas'][0].update(ancho=10,alto=10)
        plano = preparar_plano_horizontal(self.vista,'cm',.3)
        html = render_to_string('cutless/includes/board-drawing.html',
            dict(item=dict(numero=1,plano=plano),unidad_medida='cm'))
        root = ET.fromstring(html.strip())
        ns={'s':'http://www.w3.org/2000/svg'}
        self.assertTrue(any('Puerta' in ''.join(t.itertext()) for t in root.findall('.//s:title',ns)))
        labels=root.findall('.//s:text',ns)
        self.assertTrue(any(''.join(t.itertext())=='P4' and t.get('clip-path') for t in labels))
        self.assertFalse(any('Puerta' in ''.join(t.itertext()) for t in labels))
