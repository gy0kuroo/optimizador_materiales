from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from cutless.models import Optimizacion


class HistorialHorizontalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('historial_horizontal')
        self.user.perfil.preferencias_menu = {'_inicio_completado': True}
        self.user.perfil.save()
        self.client.force_login(self.user)
        self.opt = Optimizacion.objects.create(usuario=self.user, ancho_tablero=122,
            alto_tablero=244, piezas='Puerta,40,120,1', margen_corte=.3)
        self.url = reverse('cutless:api_tableros', args=[self.opt.pk])
        self.info = {'num_tableros': 1, 'num_piezas_colocadas': 1,
            'area_usada_total': 4800, 'desperdicio_total': 24968,
            'info_tableros': [{'numero': 1, 'num_piezas': 1, 'porcentaje_uso': 16.12,
                'area_usada': 4800, 'desperdicio': 24968, 'vista_web': {
                'ancho': 122, 'alto': 244,
                'catalogo': [{'numero': 1, 'nombre': 'Puerta', 'ancho': 40,
                             'alto': 120, 'cantidad': 1, 'color': '#4558E7'}],
                'piezas': [{'x': 0, 'y': 0, 'ancho': 40, 'alto': 120,
                           'numero': 1, 'nombre': 'Puerta', 'color': '#4558E7'}]}}]}

    @patch('cutless.views.exports.obtener_resultado_optimizacion')
    def test_html_compartido_conserva_imagenes_y_parametros(self, obtener):
        obtener.return_value = (['imagen'], 16.12, self.info)
        antes = Optimizacion.objects.filter(pk=self.opt.pk).values().get()
        response = self.client.get(self.url, {'presentacion': 'horizontal'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['imagenes'], ['imagen'])
        self.assertEqual(data['total'], 1)
        self.assertIn('Tablero horizontal 244', data['paneles'][0])
        self.assertIn('Detalle de piezas', data['paneles'][0])
        self.assertIn('Resumen del corte', data['paneles'][0])
        self.assertIn('P1', data['paneles'][0])
        self.assertEqual(Optimizacion.objects.filter(pk=self.opt.pk).values().get(), antes)

    @patch('cutless.views.exports.obtener_resultado_optimizacion')
    def test_api_original_no_cambia_su_respuesta(self, obtener):
        obtener.return_value = (['imagen'], 16.12, self.info)
        self.assertEqual(self.client.get(self.url).json(),
                         {'success': True, 'imagenes': ['imagen'], 'total': 1})

    @patch('cutless.views.exports.obtener_resultado_optimizacion')
    def test_no_permite_ver_otra_cuenta(self, obtener):
        otra = User.objects.create_user('otra_cuenta_horizontal')
        self.client.force_login(otra)
        self.assertEqual(self.client.get(self.url, {'presentacion': 'horizontal'}).status_code, 404)
        obtener.assert_not_called()

    def test_miniatura_horizontal_usa_coordenadas_guardadas_sin_regenerar(self):
        self.opt.imagen = 'optimizaciones/preview.png'
        self.opt.resultado_extra = {'vistas_web': {'1': self.info['info_tableros'][0]['vista_web']}}
        self.opt.save()
        antes = Optimizacion.objects.filter(pk=self.opt.pk).values().get()
        with patch('cutless.services.optimization._regenerar_grafico', side_effect=AssertionError('No recalcular')):
            response = self.client.get(reverse('cutless:historial'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'chart-thumbnail-horizontal')
        self.assertContains(response, 'primer tablero horizontal')
        self.assertContains(response, 'scrap-preview-')
        miniatura = response.context['optimizaciones_con_piezas'][0]['miniatura']['plano']
        self.assertEqual((miniatura['ancho'], miniatura['alto']), (244, 122))
        self.assertEqual(Optimizacion.objects.filter(pk=self.opt.pk).values().get(), antes)

    def test_miniatura_antigua_conserva_su_archivo_si_no_hay_coordenadas(self):
        self.opt.imagen = 'optimizaciones/preview-antigua.png'
        self.opt.save()
        response = self.client.get(reverse('cutless:historial'))
        self.assertContains(response, 'preview-antigua.png')
        self.assertNotContains(response, 'chart-thumbnail-horizontal')
        self.assertIsNone(response.context['optimizaciones_con_piezas'][0]['miniatura'])
