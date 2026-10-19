from django.test import SimpleTestCase

from cutless.models import Optimizacion
from cutless.render import generar_grafico
from cutless.services.optimization import preparar_contexto_resultado


class VistaLecturaTests(SimpleTestCase):
    def test_datos_por_tablero_corresponden_a_sus_piezas_y_numeros(self):
        imagenes, _, info = generar_grafico([(60, 100, 3)], 100, 100,
                                            nombres_piezas=['Puerta'], margen_corte=0)
        self.assertEqual(len(imagenes), 3)
        for tablero in info['info_tableros']:
            vista = tablero['vista_web']
            self.assertEqual(len(vista['piezas']), tablero['num_piezas'])
            self.assertEqual(vista['catalogo'][0]['cantidad'], 1)
            self.assertEqual(vista['catalogo'][0]['nombre'], 'Puerta')
            self.assertEqual(vista['piezas'][0]['numero'], vista['catalogo'][0]['numero'])
            self.assertEqual(vista['piezas'][0]['color'], vista['catalogo'][0]['color'])

    def test_medidas_html_se_convierten_sin_cambiar_coordenadas_guardadas(self):
        imagenes, _, info = generar_grafico([(50, 100, 1)], 100, 200,
                                            nombres_piezas=['Panel'], margen_corte=0)
        opt = Optimizacion(ancho_tablero=100, alto_tablero=200, unidad_medida='m',
                           piezas='Panel,0.5,1,1')
        contexto = preparar_contexto_resultado(opt, imagenes, info)
        tablero = contexto['tableros_con_imagenes'][0]
        self.assertEqual(tablero['catalogo'][0]['ancho'], .5)
        self.assertEqual(tablero['catalogo'][0]['alto'], 1)
        self.assertEqual(tablero['vista_web']['catalogo'][0]['ancho'], 50)
        self.assertEqual(contexto['ancho_tablero_mostrar'], 1)

    def test_resultado_antiguo_conserva_imagen_y_lista_solicitada(self):
        opt = Optimizacion(ancho_tablero=100, alto_tablero=200, piezas='Panel,50,100,3')
        contexto = preparar_contexto_resultado(opt, ['imagen-guardada'], {
            'info_tableros': [{'numero': 1, 'num_piezas': 1}]
        })
        tablero = contexto['tableros_con_imagenes'][0]
        self.assertIsNone(tablero['vista_web'])
        self.assertEqual(tablero['imagen'], 'imagen-guardada')
        self.assertEqual(tablero['catalogo'], [])
        self.assertEqual(contexto['piezas_con_nombre'][0]['cantidad'], 3)
