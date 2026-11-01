from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from cutless.models import Optimizacion


class OptimizationLoadingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('espera_optimizacion')
        self.user.perfil.preferencias_menu = {'_inicio_completado': True}
        self.user.perfil.save()
        self.client.force_login(self.user)

    def test_create_uses_optimization_skeleton_and_keeps_download_spinner(self):
        response = self.client.get(reverse('cutless:index'))
        self.assertContains(response, 'data-loading-optimization')
        self.assertContains(response, 'cutless-optimization-loading-template')
        self.assertContains(response, 'optimization-loading.js')
        self.assertContains(response, 'cutless-loading-template')
        self.assertNotContains(response, 'onsubmit="mostrarIndicadorCarga')

    def test_edit_uses_same_loading_contract(self):
        opt = Optimizacion.objects.create(usuario=self.user, ancho_tablero=122, alto_tablero=244, piezas='P,25,25,5')
        response = self.client.get(reverse('cutless:editar_optimizacion', args=[opt.pk]))
        self.assertContains(response, 'data-loading-optimization')
        self.assertContains(response, 'cutless-optimization-loading-template')
        self.assertContains(response, 'optimization-loading.css')

    def test_result_covers_all_sections_and_conditional_costs(self):
        from django.template.loader import render_to_string
        from django.test import RequestFactory
        from decimal import Decimal
        opt = Optimizacion.objects.create(usuario=self.user, ancho_tablero=122, alto_tablero=244, piezas='P,25,25,5')
        request = RequestFactory().get('/')
        request.user = self.user
        request.session = {}
        base = {'optimizacion': opt, 'num_tableros': 1, 'unidad_medida': 'cm',
                'tableros_con_imagenes': [{'numero': 1, 'info': {'porcentaje_uso': 50}}],
                'info_desperdicio': {'info_tableros': [], 'num_piezas_colocadas': 5}}
        for price, labor, total in [(None, 0, None), (None, 500, None), (Decimal('1000'), 500, Decimal('1500'))]:
            with self.subTest(price=price, labor=labor):
                html = render_to_string('cutless/resultado.html', {**base, 'precio_tablero': price,
                    'mano_obra': labor, 'costo_total': total}, request=request)
                for stage in ['header', 'total', 'navigation', 'drawing', 'summary', 'pieces', 'technical', 'fold', 'actions']:
                    self.assertIn(f'data-result-stage="{stage}"', html)
                    self.assertIn(f'data-result-placeholder="{stage}"', html)
                self.assertEqual('data-result-stage="costs"' in html, bool(price or labor or total))
                self.assertIn('result-reveal.js', html)
                if price or labor or total:
                    self.assertLess(html.index('data-result-stage="technical"'), html.index('data-result-stage="costs"'))
                    self.assertLess(html.index('data-result-stage="costs"'), html.index('data-result-stage="fold"'))
                    self.assertIn('result-costs-title-1', html)
                self.assertNotIn('Prepara otro corte o consulta tus trabajos guardados.', html)

                self.assertNotIn('<details class="result-details" data-result-stage="fold" open', html)
