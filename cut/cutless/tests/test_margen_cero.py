from types import SimpleNamespace

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from cutless.models import Optimizacion
from cutless.render import _info_desperdicio_desde_optimizacion
from cutless.services.optimization import _regenerar_grafico


class MargenCeroTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('margen_user')
        self.client.force_login(self.usuario)
        self.data = {
            'unidad_medida': 'cm', 'ancho': 100, 'alto': 100,
            'permitir_rotacion': 'on', 'margen_corte': 0,
            'form-TOTAL_FORMS': 1, 'form-INITIAL_FORMS': 0,
            'form-MIN_NUM_FORMS': 0, 'form-MAX_NUM_FORMS': 20,
            'form-0-nombre': 'Cuadrado', 'form-0-ancho': 50,
            'form-0-alto': 50, 'form-0-cantidad': 4,
        }

    def crear_optimizacion(self, margen=0):
        return Optimizacion.objects.create(
            usuario=self.usuario, ancho_tablero=100, alto_tablero=100,
            piezas='Cuadrado,50,50,4', margen_corte=margen,
        )

    def test_crear_con_cero_usa_un_tablero(self):
        response = self.client.post(reverse('cutless:index'), self.data)
        self.assertEqual(response.status_code, 200)
        opt = Optimizacion.objects.get(usuario=self.usuario)
        self.assertEqual(opt.margen_corte, 0)
        self.assertEqual(opt.num_tableros, 1)
        self.assertEqual(opt.tableros.count(), 1)
        self.assertEqual(opt.aprovechamiento_total, 100)

    def test_editar_con_cero_usa_un_tablero(self):
        opt = self.crear_optimizacion(0.3)
        response = self.client.post(reverse('cutless:editar_optimizacion', args=[opt.pk]), self.data)
        self.assertEqual(response.status_code, 200)
        opt.refresh_from_db()
        self.assertEqual(opt.margen_corte, 0)
        self.assertEqual(opt.num_tableros, 1)
        self.assertEqual(opt.tableros.count(), 1)

    def test_crear_con_campo_vacio_o_positivo_conserva_margen(self):
        for valor, esperado in [('', 0.3), (3, 0.3), (1, 0.1)]:
            with self.subTest(valor=valor):
                response = self.client.post(reverse('cutless:index'), dict(self.data, margen_corte=valor))
                self.assertEqual(response.status_code, 200)
                opt = Optimizacion.objects.filter(usuario=self.usuario).latest('pk')
                self.assertAlmostEqual(opt.margen_corte, esperado)
                self.assertEqual(opt.num_tableros, 4)

    def test_editar_con_campo_vacio_conserva_default(self):
        opt = self.crear_optimizacion()
        response = self.client.post(reverse('cutless:editar_optimizacion', args=[opt.pk]), dict(self.data, margen_corte=''))
        self.assertEqual(response.status_code, 200)
        opt.refresh_from_db()
        self.assertEqual(opt.margen_corte, 0.3)
        self.assertEqual(opt.num_tableros, 4)

    def test_regenerar_grafico_con_cero_usa_un_tablero(self):
        imagenes, aprovechamiento, info = _regenerar_grafico(self.crear_optimizacion())
        self.assertEqual(len(imagenes), 1)
        self.assertEqual(aprovechamiento, 100)
        self.assertEqual(info['num_piezas_colocadas'], 4)

    def test_regenerar_estadisticas_con_cero_usa_un_tablero(self):
        info = _info_desperdicio_desde_optimizacion(self.crear_optimizacion())
        self.assertEqual(info['num_tableros'], 1)
        self.assertEqual(info['desperdicio_total'], 0)

    def test_imprimir_plan_con_cero_usa_un_tablero(self):
        opt = self.crear_optimizacion()
        response = self.client.get(reverse('cutless:imprimir_plan_corte', args=[opt.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['num_tableros'], 1)

    def test_registros_sin_margen_usan_default(self):
        for valor in (None, 'ausente'):
            with self.subTest(valor=valor):
                opt = SimpleNamespace(piezas='50,50,4', unidad_medida='cm', ancho_tablero=100, alto_tablero=100)
                if valor is None:
                    opt.margen_corte = None
                self.assertEqual(_info_desperdicio_desde_optimizacion(opt)['num_tableros'], 4)
                self.assertEqual(len(_regenerar_grafico(opt)[0]), 4)
