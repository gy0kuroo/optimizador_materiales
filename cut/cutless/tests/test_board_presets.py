import base64
import io
from unittest.mock import patch
from PIL import Image
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from cutless.board_presets import descripcion_material
from cutless.forms import TableroForm
from cutless.models import Material, Optimizacion
from cutless.services.optimization import persistir_resultado_optimizacion
from cutless.services.comparison import comparar_trabajos


class BoardPresetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('presets')
        self.user.perfil.rol = 'admin'
        self.user.perfil.preferencias_menu = {'_inicio_completado': True}
        self.user.perfil.save()
        self.client.force_login(self.user)
        self.opt = Optimizacion(usuario=self.user, ancho_tablero=122, alto_tablero=244,
                               piezas='P,10,10,1', num_tableros=1)
        image = io.BytesIO()
        Image.new('RGB', (2, 2), 'white').save(image, format='PNG')
        self.images = [base64.b64encode(image.getvalue()).decode()]
        self.info = {'area_usada_total': 100, 'desperdicio_total': 29668,
             'num_piezas_solicitadas': 1, 'num_piezas_colocadas': 1,
             'info_tableros': [{'numero': 1, 'area_usada': 100, 'desperdicio': 29668,
              'porcentaje_uso': .336, 'num_piezas': 1, 'vista_web': {
                'ancho': 122, 'alto': 244,
                'catalogo': [{'numero': 1, 'nombre': 'P', 'ancho': 10, 'alto': 10, 'cantidad': 1, 'color': '#FF6B6B'}],
                'piezas': [{'numero': 1, 'nombre': 'P', 'x': 0, 'y': 0, 'ancho': 10, 'alto': 10, 'color': '#FF6B6B'}]}}]}

    def test_standard_material_persists_without_library_and_survives_refresh(self):
        persistir_resultado_optimizacion(self.opt, self.images, self.info, .336, medida_habitual='osb-122x244')
        self.opt.refresh_from_db()
        self.assertIsNone(self.opt.material_id)
        self.assertEqual(descripcion_material(self.opt)['nombre'], 'OSB')
        persistir_resultado_optimizacion(self.opt, self.images, self.info, .336)
        self.opt.refresh_from_db()
        self.assertEqual(self.opt.resultado_extra['medida_habitual'], 'osb-122x244')
        for route in ('editar_optimizacion', 'duplicar_optimizacion'):
            response = self.client.get(reverse('cutless:' + route, args=[self.opt.pk]))
            self.assertEqual(response.context['tablero_form']['medida_habitual'].value(), 'osb-122x244')

    def test_manual_dimensions_do_not_infer_osb_or_mdf(self):
        data = descripcion_material(self.opt)
        self.assertEqual(data['nombre'], 'Tablero de medidas habituales')
        self.assertIsNone(data['identidad'])
        self.assertEqual(data['origen'], 'Tipo de material no registrado')

    def test_library_material_takes_precedence_over_preset(self):
        material = Material.objects.create(usuario=self.user, nombre='MDF 18 mm', ancho=122, alto=244)
        self.opt.material = material
        self.opt.resultado_extra = {'medida_habitual': 'osb-122x244'}
        self.assertEqual(descripcion_material(self.opt)['nombre'], 'MDF 18 mm')

    def test_preset_is_validated_against_dimensions_and_unit(self):
        data = dict(unidad_medida='m', ancho='1.22', alto='2.44', margen_corte=3, medida_habitual='osb-122x244')
        form = TableroForm(data, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['medida_habitual'], 'osb-122x244')
        form = TableroForm({**data, 'ancho': '1.5'}, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['medida_habitual'], '')
        self.assertFalse(TableroForm({**data, 'medida_habitual': 'inexistente'}, user=self.user).is_valid())

    def test_explicit_removal_clears_stored_preset(self):
        persistir_resultado_optimizacion(self.opt, self.images, self.info, .336, medida_habitual='osb-122x244')
        persistir_resultado_optimizacion(self.opt, self.images, self.info, .336, medida_habitual='')
        self.opt.refresh_from_db()
        self.assertNotIn('medida_habitual', self.opt.resultado_extra)

    def test_create_from_standard_and_comparison_chart_without_price(self):
        self.user.perfil.rol = 'usuario'
        self.user.perfil.save()
        data = {'ancho': 122, 'alto': 244, 'unidad_medida': 'cm', 'medida_habitual': 'osb-122x244',
                'margen_corte': 3, 'form-TOTAL_FORMS': 1, 'form-INITIAL_FORMS': 0,
                'form-0-nombre': 'P', 'form-0-ancho': 10, 'form-0-alto': 10, 'form-0-cantidad': 1}
        with patch('cutless.views.optimization.generar_grafico', return_value=(self.images, .336, self.info)):
            response = self.client.post(reverse('cutless:index'), data)
        self.assertIn(response.status_code, (200, 302))
        opt = Optimizacion.objects.get(usuario=self.user)
        self.assertEqual(opt.resultado_extra['medida_habitual'], 'osb-122x244')
        other = Optimizacion.objects.create(usuario=self.user, ancho_tablero=122, alto_tablero=244,
                    piezas='P,10,10,1', num_tableros=1)
        response = self.client.get(reverse('cutless:comparar_optimizaciones'), {'opt1': opt.pk, 'opt2': other.pk})
        html = response.content.decode()
        self.assertLess(html.index('Gráficos de comparación'), html.index('Comparación de recursos'))
        self.assertContains(response, 'El gráfico de costos no está disponible')
        self.assertContains(response, 'Selección estándar; sin ficha ni precio de biblioteca')
        self.assertEqual(len(response.context['comparacion']['graficos']), 1)

    def test_material_json_distinguishes_zero_price_from_absent_price(self):
        from cutless.views.common import _materiales_data_index
        material = Material.objects.create(usuario=self.user, nombre='Precio cero', ancho=122, alto=244, precio=0)
        self.assertEqual(_materiales_data_index(self.user)[str(material.pk)]['precio'], 0)
