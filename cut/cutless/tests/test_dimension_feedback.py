from django.test import SimpleTestCase, TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from cutless.forms import TableroForm, PiezaForm
from cutless.models import Optimizacion


class MedidasPorUnidadTests(SimpleTestCase):
    def test_cantidad_limita_enteros_por_tipo(self):
        datos = {'ancho': '30', 'alto': '40'}
        for cantidad in ('1', '50', '100'):
            form = PiezaForm({**datos, 'cantidad': cantidad})
            self.assertTrue(form.is_valid(), form.errors)
        for cantidad in ('0', '-1', '101', '1246545654', '1.5', 'abc'):
            form = PiezaForm({**datos, 'cantidad': cantidad})
            self.assertFalse(form.is_valid())
            self.assertEqual(set(form.errors), {'cantidad'})
        form = PiezaForm(datos)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['cantidad'], 1)

    def test_sierra_limites_siempre_en_mm(self):
        for unit, dimension in [('m', '1'), ('cm', '100'), ('in', '40')]:
            datos = {'unidad_medida': unit, 'ancho': dimension, 'alto': dimension}
            for margen in ('0', '3', '10'):
                form = TableroForm({**datos, 'margen_corte': margen})
                self.assertTrue(form.is_valid(), form.errors)
            for margen in ('11', '-1', 'abc'):
                form = TableroForm({**datos, 'margen_corte': margen})
                self.assertFalse(form.is_valid())
                self.assertIn('mm', str(form.errors['margen_corte']))
                self.assertEqual(set(form.errors), {'margen_corte'})

    def test_mil_metros_indica_campo_valor_y_maximo_sin_error_falso_de_ausencia(self):
        form = TableroForm({'unidad_medida': 'm', 'ancho': '1000', 'alto': '2.44'})
        self.assertFalse(form.is_valid())
        mensaje = str(form.errors['ancho'])
        self.assertIn('1000 m', mensaje)
        self.assertIn('de 0,1 a 3 m', mensaje)
        self.assertIn('demasiado alto', mensaje)
        self.assertNotIn('alto', form.errors)
        self.assertFalse(form.non_field_errors())

    def test_tablero_acepta_equivalencias_y_limites(self):
        for unit, ancho, alto in [('cm', '122', '244'), ('m', '1.22', '2.44'),
                                 ('mm', '1220', '2440'), ('in', '48', '96'), ('ft', '4', '8')]:
            with self.subTest(unit=unit):
                self.assertTrue(TableroForm({'unidad_medida': unit, 'ancho': ancho, 'alto': alto}).is_valid())
        for value in ('0.1', '3'):
            self.assertTrue(TableroForm({'unidad_medida': 'm', 'ancho': value, 'alto': value}).is_valid())

    def test_rechaza_ambos_lados_con_errores_independientes(self):
        form = TableroForm({'unidad_medida': 'm', 'ancho': '1000', 'alto': '-1'})
        self.assertFalse(form.is_valid())
        self.assertEqual(set(form.errors), {'ancho', 'alto'})
        self.assertIn('demasiado bajo', str(form.errors['alto']))

    def test_numero_invalido_no_se_presenta_como_campo_vacio(self):
        form = TableroForm({'unidad_medida': 'm', 'ancho': 'abc', 'alto': '2'})
        self.assertFalse(form.is_valid())
        self.assertIn('número válido', str(form.errors['ancho']))
        self.assertFalse(form.non_field_errors())

    def test_pieza_milimetros_acepta_mas_de_300_sin_superar_300_cm(self):
        form = PiezaForm({'unidad_medida': 'mm', 'ancho': '1000', 'alto': '2000', 'cantidad': 1})
        self.assertTrue(form.is_valid(), form.errors)
        form = PiezaForm({'unidad_medida': 'm', 'ancho': '1000', 'alto': '2', 'cantidad': 1})
        self.assertFalse(form.is_valid())
        self.assertIn('de 0,001 a 3 m', str(form.errors['ancho']))

    def test_limites_visibles_en_pulgadas_y_pies_son_admisibles(self):
        for unit, minimo, maximo in [('in', '3.937008', '118.110236'), ('ft', '.328084', '9.842519')]:
            form = TableroForm({'unidad_medida': unit, 'ancho': minimo, 'alto': maximo})
            self.assertTrue(form.is_valid(), form.errors)


class AvisosMedidasViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('medidas_claras')
        self.client.force_login(self.user)
        self.data = {'unidad_medida': 'm', 'ancho': '1000', 'alto': '2.44',
            'form-TOTAL_FORMS': '1', 'form-INITIAL_FORMS': '0',
            'form-0-ancho': '.3', 'form-0-alto': '.4', 'form-0-cantidad': '1'}

    def test_inicio_muestra_error_concreto_y_conserva_valores(self):
        response = self.client.post(reverse('cutless:index'), self.data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ingresaste 1000 m')
        self.assertContains(response, 'de 0,1 a 3 m')
        self.assertEqual(response.context['tablero_form']['ancho'].value(), '1000')
        self.assertFalse(Optimizacion.objects.exists())

    def test_edicion_no_altera_resultado_con_medidas_invalidas(self):
        opt = Optimizacion.objects.create(usuario=self.user, ancho_tablero=122, alto_tablero=244, piezas='30,40,1')
        response = self.client.post(reverse('cutless:editar_optimizacion', args=[opt.pk]), self.data)
        self.assertContains(response, 'ingresaste 1000 m')
        opt.refresh_from_db()
        self.assertEqual(opt.ancho_tablero, 122)
