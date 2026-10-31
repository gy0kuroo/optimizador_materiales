from copy import deepcopy
from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from cutless.models import Optimizacion, TableroOptimizacion


class ViewerLoadingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('visor_ligero')
        self.user.perfil.preferencias_menu = {'_inicio_completado': True}
        self.user.perfil.save()
        self.client.force_login(self.user)
        vista = {'ancho': 122, 'alto': 244,
                 'catalogo': [{'numero': 1, 'nombre': 'Puerta', 'ancho': 40, 'alto': 120, 'cantidad': 1, 'color': '#4558E7'}],
                 'piezas': [{'numero': 1, 'nombre': 'Puerta', 'x': 0, 'y': 0, 'ancho': 40, 'alto': 120, 'color': '#4558E7'}]}
        self.opt = Optimizacion.objects.create(usuario=self.user, ancho_tablero=122, alto_tablero=244,
            piezas='Puerta,40,120,3', margen_corte=.3, num_tableros=3, resultado_generado=True,
            area_usada_total=14400, desperdicio_total=74904,
            resultado_extra={'vistas_web': {str(n): deepcopy(vista) for n in range(1,4)},
                'num_piezas_colocadas': 3, 'num_piezas_solicitadas': 3})
        for n in range(1,4):
            TableroOptimizacion.objects.create(optimizacion=self.opt, numero=n,
                area_usada=4800, desperdicio=24968, porcentaje_uso=16.12, num_piezas=1)
        self.url = reverse('cutless:api_tableros', args=[self.opt.pk])

    def test_visor_returns_only_requested_board_without_png_or_recalculation(self):
        before = Optimizacion.objects.filter(pk=self.opt.pk).values().get()
        with patch('cutless.exports.board_png.generar_png_tablero', side_effect=AssertionError('No generar PNG')):
            with patch('cutless.services.optimization._regenerar_grafico', side_effect=AssertionError('No recalcular')):
                response = self.client.get(self.url, {'modo': 'visor', 'presentacion': 'horizontal', 'tablero': 2})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual((data['numero'], data['total'], data['modo']), (2, 3, 'geometria'))
        self.assertNotIn('imagenes', data)
        self.assertNotIn('paneles', data)
        self.assertIn('Información del tablero 2', data['panel'])
        self.assertIn('Tableros usados', data['panel'])
        self.assertIn('svg', data['panel'])
        self.assertEqual(data['panel'].count('class="cut-layout"'), 1)
        self.assertEqual(Optimizacion.objects.filter(pk=self.opt.pk).values().get(), before)
        self.assertEqual(response['Cache-Control'], 'private, no-store')

    def test_visor_preserves_overall_totals_in_single_board_context(self):
        from cutless.services.optimization import contexto_tablero_visor
        context = contexto_tablero_visor(self.opt, 2)
        self.assertEqual(context['num_tableros'], 3)
        self.assertEqual(len(context['tableros_con_imagenes']), 1)
        self.assertEqual(context['info_desperdicio']['num_piezas_colocadas'], 3)
        self.assertEqual(context['info_desperdicio']['area_usada_total'], 14400)

    def test_visor_rejects_invalid_board_and_other_owners(self):
        for value, code in [('incorrecto',400), ('0',404), ('4',404)]:
            self.assertEqual(self.client.get(self.url, {'modo':'visor', 'tablero':value}).status_code, code)
        self.client.force_login(User.objects.create_user('otro_visor'))
        self.assertEqual(self.client.get(self.url, {'modo':'visor', 'tablero':1}).status_code,404)

    def test_history_includes_reserved_placeholders_and_recovery(self):
        response = self.client.get(reverse('cutless:historial'))
        for text in ('history-skeleton-drawing', 'history-skeleton-summary', 'history-skeleton-technical',
                     'history-skeleton-pieces', 'history-board-retry', 'board-loading.css'):
            self.assertContains(response, text)
