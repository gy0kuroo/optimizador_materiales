from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from cutless.forms import PlantillaForm
from cutless.models import Plantilla


class PlantillasTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('plantillero')
        self.usuario.perfil.rol = 'admin'
        self.usuario.perfil.save()
        self.client.force_login(self.usuario)
        self.datos = {'nombre': 'Armario', 'categoria': 'muebles',
                      'ancho_tablero': '1.22', 'alto_tablero': '2.44',
                      'unidad_medida': 'm', 'piezas': 'Puerta,0.5,1,2',
                      'permitir_rotacion': 'on', 'margen_corte': '0'}

    def test_medidas_y_margen_se_conservan_al_crear_editar_y_cargar(self):
        self.client.post(reverse('cutless:crear_plantilla'), self.datos)
        plantilla = Plantilla.objects.get(usuario=self.usuario)
        self.assertAlmostEqual(plantilla.ancho_tablero, 122)
        self.assertAlmostEqual(plantilla.alto_tablero, 244)
        self.assertEqual(plantilla.margen_corte, 0)
        form = PlantillaForm(instance=plantilla, user=self.usuario)
        self.assertAlmostEqual(form.initial['ancho_tablero'], 1.22)
        self.assertEqual(form.initial['margen_corte'], 0)
        self.client.post(reverse('cutless:editar_plantilla', args=[plantilla.pk]), self.datos)
        plantilla.refresh_from_db()
        self.assertAlmostEqual(plantilla.ancho_tablero, 122)
        response = self.client.get(reverse('cutless:usar_plantilla', args=[plantilla.pk]))
        self.assertAlmostEqual(response.context['tablero_form']['ancho'].value(), 1.22)
        self.assertEqual(response.context['tablero_form']['margen_corte'].value(), 0)

    def test_personalizar_sistema_crea_copia_sin_modificar_original(self):
        original = Plantilla.objects.create(nombre='Sistema', es_predefinida=True,
                                           ancho_tablero=100, alto_tablero=200,
                                           piezas='Puerta,20,30,1')
        response = self.client.post(reverse('cutless:editar_plantilla', args=[original.pk]), self.datos)
        self.assertRedirects(response, reverse('cutless:lista_plantillas'))
        original.refresh_from_db()
        self.assertEqual(original.nombre, 'Sistema')
        self.assertEqual(original.ancho_tablero, 100)
        self.assertTrue(original.es_predefinida)
        copia = Plantilla.objects.get(usuario=self.usuario)
        self.assertFalse(copia.es_predefinida)

    def test_nombre_duplicado_y_numeros_no_finitos_se_rechazan(self):
        self.client.post(reverse('cutless:crear_plantilla'), self.datos)
        form = PlantillaForm(self.datos, user=self.usuario)
        self.assertFalse(form.is_valid())
        self.assertIn('nombre', form.errors)
        for cambio in ({'piezas': 'Puerta,nan,1,2'}, {'margen_corte': '11'},
                       {'ancho_tablero': '-1'}):
            with self.subTest(cambio=cambio):
                self.assertFalse(PlantillaForm({**self.datos, 'nombre': 'Otra', **cambio},
                                              user=self.usuario).is_valid())

    def test_plantilla_ajena_no_se_puede_editar_ni_cargar(self):
        otra = User.objects.create_user('otroplantillero')
        plantilla = Plantilla.objects.create(usuario=otra, nombre='Privada',
                                            ancho_tablero=100, alto_tablero=200, piezas='Puerta,20,30,1')
        for ruta in ('editar_plantilla', 'usar_plantilla'):
            self.assertRedirects(self.client.get(reverse('cutless:' + ruta, args=[plantilla.pk])),
                                 reverse('cutless:lista_plantillas'))
