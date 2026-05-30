from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from cutless.models import Optimizacion


class IndexOptimizacionTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('carpintero', password='test12345')
        self.usuario.perfil.rol = 'usuario'
        self.usuario.perfil.save()

    def test_index_post_muestra_resultado_sin_error(self):
        self.client.login(username='carpintero', password='test12345')
        data = {
            'unidad_medida': 'cm',
            'ancho': 122,
            'alto': 244,
            'permitir_rotacion': 'on',
            'margen_corte': 3,
            'form-TOTAL_FORMS': 1,
            'form-INITIAL_FORMS': 0,
            'form-MIN_NUM_FORMS': 0,
            'form-MAX_NUM_FORMS': 20,
            'form-0-nombre': 'Puerta',
            'form-0-ancho': 60,
            'form-0-alto': 40,
            'form-0-cantidad': 1,
        }
        response = self.client.post(reverse('cutless:index'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cutless/resultado.html')
        self.assertContains(response, 'aprovechamiento')
        optimizacion = Optimizacion.objects.get(usuario=self.usuario)
        self.assertGreater(optimizacion.aprovechamiento_total, 0)
        self.assertGreater(optimizacion.area_usada_total, 0)
