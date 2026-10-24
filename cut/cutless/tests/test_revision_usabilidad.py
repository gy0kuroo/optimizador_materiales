"""Regresiones detectadas durante la evaluación de usabilidad."""
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from cutless.models import Optimizacion


class RevisionUsabilidadTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('revision_pruebas')
        self.client.force_login(self.user)

    def test_duplicar_conserva_tablero_y_piezas_en_unidad_original(self):
        for unidad, ancho, alto in [('cm', '122.0', '244.0'), ('m', '1.22', '2.44')]:
            with self.subTest(unidad=unidad):
                opt = Optimizacion.objects.create(usuario=self.user, ancho_tablero=122,
                    alto_tablero=244, unidad_medida=unidad, piezas='Puerta,0.4,1.2,2',
                    margen_corte=.25, permitir_rotacion=False)
                response = self.client.get(reverse('cutless:duplicar_optimizacion', args=[opt.pk]))
                self.assertContains(response, f'value="{ancho}"')
                self.assertContains(response, f'value="{alto}"')
                form = response.context['tablero_form']
                self.assertEqual(form['margen_corte'].value(), 2.5)
                self.assertFalse(form['permitir_rotacion'].value())
                self.assertEqual(response.context['pieza_formset'].forms[0]['ancho'].value(), .4)


    def test_exportaciones_no_recalculan_impresion_y_conservan_color(self):
        opt = Optimizacion.objects.create(usuario=self.user, ancho_tablero=122,
            alto_tablero=244, piezas='Puerta,40,120,2')
        info = {'info_tableros': [], 'area_usada_total': 0, 'desperdicio_total': 0}
        with patch('cutless.views.exports.obtener_resultado_optimizacion', return_value=([], 0, info)):
            response = self.client.get(reverse('cutless:imprimir_plan_corte', args=[opt.pk]))
        self.assertEqual(response.status_code, 200)
