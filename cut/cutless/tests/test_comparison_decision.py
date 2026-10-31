from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from cutless.models import Optimizacion
from cutless.services.comparison import comparar_trabajos


class ComparisonDecisionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('alternativas')
        self.user.perfil.rol = 'admin'
        self.user.perfil.save()
        self.client.force_login(self.user)

    def opt(self, **kwargs):
        valores = dict(usuario=self.user, ancho_tablero=122, alto_tablero=244,
                       piezas='Puerta,30,40,2', num_tableros=1, aprovechamiento_total=80)
        return Optimizacion.objects.create(**{**valores, **kwargs})

    def test_equivalence_ignores_order_units_case_spaces_and_split_quantities(self):
        a = self.opt(piezas='Puerta,30,40,2\nRepisa,20,40,3')
        b = self.opt(unidad_medida='m', piezas='REPISA,0.2,0.4,3\n puerta ,0.3,0.4,1\nPuerta,0.3,0.4,1')
        result = comparar_trabajos(a, b)
        self.assertTrue(result['equivalentes'])
        self.assertEqual(result['a']['cantidad'], 5)
        self.assertEqual(result['a']['piezas'], Decimal('.48'))

    def test_different_demands_do_not_generate_recommendations(self):
        a, b = self.opt(), self.opt(piezas='Puerta,30,40,3')
        result = comparar_trabajos(a, b)
        self.assertFalse(result['equivalentes'])
        self.assertEqual(result['conclusiones'], [])

    def test_requested_orientation_is_not_silently_swapped(self):
        result = comparar_trabajos(self.opt(), self.opt(piezas='Puerta,40,30,2'))
        self.assertFalse(result['equivalentes'])

    def test_fewer_boards_can_require_more_material(self):
        a = self.opt(ancho_tablero=100, alto_tablero=100, num_tableros=3)
        b = self.opt(ancho_tablero=200, alto_tablero=200, num_tableros=2)
        result = comparar_trabajos(a, b)
        self.assertEqual(result['diferencia_area'], Decimal(5))
        self.assertIn('alternativa A necesita 5,00', result['conclusiones'][0])
        self.assertIn('alternativa B utiliza 1', result['conclusiones'][1])

    def test_zero_price_is_valid_missing_price_omits_cost_chart(self):
        a, b = self.opt(precio_tablero=0), self.opt(precio_tablero=None)
        result = comparar_trabajos(a, b)
        self.assertEqual(result['a']['costo'], Decimal(0))
        self.assertIsNone(result['diferencia_costo'])
        self.assertEqual(len(result['graficos']), 1)
        self.assertTrue(any('falta el precio' in texto for texto in result['conclusiones']))

    def test_cost_difference_and_saw_conversion(self):
        result = comparar_trabajos(self.opt(precio_tablero=100, margen_corte=.3), self.opt(precio_tablero=80))
        self.assertEqual(result['diferencia_costo'], Decimal(-20))
        self.assertEqual(result['a']['sierra_mm'], Decimal(3))
        self.assertEqual(len(result['graficos']), 2)
        self.assertTrue(all(0 <= bar['ancho'] <= 100 for graph in result['graficos'] for bar in graph['barras']))

    def test_invalid_saved_pieces_do_not_produce_equivalence(self):
        for texto in ('P,nan,30,1', 'P,30,40,-1', 'datos inválidos'):
            result = comparar_trabajos(self.opt(), self.opt(piezas=texto))
            self.assertFalse(result['equivalentes'])
            self.assertEqual(result['conclusiones'], [])

    def test_page_explains_equivalence_and_keeps_selector(self):
        a, b = self.opt(), self.opt(unidad_medida='m', piezas='Puerta,0.3,0.4,2')
        response = self.client.get(reverse('cutless:comparar_optimizaciones'), {'opt1': a.pk, 'opt2': b.pk})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['comparacion']['equivalentes'])
        self.assertContains(response, 'Comparación de recursos')
        self.assertContains(response, 'name="opt1"')
        self.assertContains(response, 'Material necesario')
