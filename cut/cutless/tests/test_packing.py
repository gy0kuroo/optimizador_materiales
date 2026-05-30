from django.contrib.auth.models import User
from django.test import TestCase

from cutless.models import Optimizacion
from cutless.packing import (
    INFO_DESPERDICIO_CAMPOS,
    normalizar_info_desperdicio,
    optimizar_corte,
    pieza_cabe_en_tablero,
)
from cutless.render import generar_grafico
from cutless.services.optimization import preparar_contexto_resultado


class PackingTests(TestCase):
    def test_pieza_cabe_con_rotacion(self):
        self.assertTrue(pieza_cabe_en_tablero(80, 200, 122, 244, True))
        self.assertFalse(pieza_cabe_en_tablero(300, 300, 122, 244, True))

    def test_optimizar_corte_coloca_piezas(self):
        piezas = [(50, 30, 1), (20, 20, 2)]
        tableros, aprov, info = optimizar_corte(
            piezas, 122, 244, nombres_piezas=['A', 'B'],
        )
        self.assertEqual(len(tableros), 1)
        self.assertEqual(info['num_piezas_colocadas'], 3)
        self.assertGreater(aprov, 0)

    def test_pieza_demasiado_grande_no_colocada(self):
        piezas = [(500, 500, 1)]
        tableros, aprov, info = optimizar_corte(piezas, 122, 244)
        self.assertEqual(len(tableros), 0)
        self.assertEqual(len(info['piezas_no_colocadas']), 1)
        self.assertEqual(aprov, 0)

    def test_generar_grafico_usa_motor(self):
        piezas = [(60, 40, 1)]
        imagenes, aprov, info = generar_grafico(
            piezas, 122, 244, 'cm', nombres_piezas=['Puerta'],
        )
        self.assertEqual(len(imagenes), 1)
        self.assertTrue(imagenes[0])
        self.assertEqual(info['num_piezas_colocadas'], 1)
        self.assertIn('area_usada_total', info)

    def test_preparar_contexto_resultado_con_info_completa(self):
        user = User.objects.create_user(username='pack_test', password='test12345')
        piezas = [(60, 40, 1)]
        imagenes, _, info = generar_grafico(
            piezas, 122, 244, 'cm', nombres_piezas=['Puerta'],
        )
        optimizacion = Optimizacion.objects.create(
            usuario=user,
            ancho_tablero=122,
            alto_tablero=244,
            unidad_medida='cm',
            piezas='Puerta,60,40,1',
        )
        contexto = preparar_contexto_resultado(optimizacion, imagenes, info)
        self.assertIn('area_usada_total', contexto['info_desperdicio'])
        self.assertGreater(contexto['info_desperdicio']['area_usada_total'], 0)

    def test_preparar_contexto_tolera_info_por_tablero(self):
        user = User.objects.create_user(username='pack_test2', password='test12345')
        piezas = [(60, 40, 1)]
        imagenes, _, info = generar_grafico(
            piezas, 122, 244, 'cm', nombres_piezas=['Puerta'],
        )
        info_incompleta = info['info_tableros'][0]
        optimizacion = Optimizacion.objects.create(
            usuario=user,
            ancho_tablero=122,
            alto_tablero=244,
            unidad_medida='cm',
            piezas='Puerta,60,40,1',
        )
        contexto = preparar_contexto_resultado(optimizacion, imagenes, info_incompleta)
        self.assertGreater(contexto['info_desperdicio']['area_usada_total'], 0)

    def test_contrato_info_desperdicio_optimizar_corte(self):
        piezas = [(50, 30, 2)]
        _, _, info = optimizar_corte(piezas, 122, 244)
        for campo in INFO_DESPERDICIO_CAMPOS:
            self.assertIn(campo, info, msg=f'Falta {campo}')

    def test_contrato_info_desperdicio_generar_grafico(self):
        piezas = [(50, 30, 1)]
        _, _, info = generar_grafico(piezas, 122, 244, 'cm')
        for campo in INFO_DESPERDICIO_CAMPOS:
            self.assertIn(campo, info, msg=f'Falta {campo}')

    def test_normalizar_info_desperdicio_dict_parcial(self):
        parcial = {'numero': 1, 'area_usada': 100, 'desperdicio': 200, 'num_piezas': 2}
        info = normalizar_info_desperdicio(parcial)
        for campo in INFO_DESPERDICIO_CAMPOS:
            self.assertIn(campo, info)
        self.assertEqual(info['area_usada_total'], 100)
        self.assertEqual(info['desperdicio_total'], 200)
